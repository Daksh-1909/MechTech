"""Diagnostic Orchestrator Service: Hybrid reasoning combining Rules, ML, and Knowledge Graph."""

from datetime import datetime
from typing import Any
import uuid

import joblib
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.core.time import utcnow
from app.ml.baseline_model import predict_window, train_baseline_classifier
from app.ml.features import build_features
from app.ml.service import load_artifact, models_root
from app.models import Diagnosis, User
from app.models.enums import DiagnosisStatus, EvidenceType, ReviewStatus, Severity
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.diagnostics import repository
from app.modules.diagnostics.schemas import (
    DiagnosisEvidenceResponse,
    DiagnosisGenerateRequest,
    DiagnosisResponse,
    DiagnosisReviewRequest,
)
from app.modules.equipment import service as eq_service
from app.modules.knowledge_graph.engine import KnowledgeGraphEngine
from app.modules.monitoring import repository as rule_repo
from app.modules.sensors import reading_repository as reading_repo


def _is_platform_admin(user: User) -> bool:
    return any(
        a.role and a.role.key in {"platform_admin", "admin"}
        for a in getattr(user, "assigned_roles", [])
    )


def _get_or_create_ml_model_bundle() -> dict[str, Any]:
    """Retrieve the cached baseline Random Forest classifier or train it on demand."""
    model_path = models_root() / "motor_fault_classifier_v1.joblib"
    if not model_path.exists():
        _, _, model_path = train_baseline_classifier()
    return joblib.load(model_path)


def _build_diagnosis_response(diag: Diagnosis) -> DiagnosisResponse:
    ev_items = [
        DiagnosisEvidenceResponse(
            id=ev.id,
            evidence_type=ev.evidence_type,
            source_reference=ev.source_reference,
            weight=ev.weight,
            details_json=ev.details_json,
            created_at=ev.created_at,
        )
        for ev in getattr(diag, "evidence_items", [])
    ]

    fault_key = diag.primary_fault.key if diag.primary_fault else None
    fault_name = diag.primary_fault.name if diag.primary_fault else None

    return DiagnosisResponse(
        id=diag.id,
        organization_id=diag.organization_id,
        equipment_id=diag.equipment_id,
        primary_fault_id=diag.primary_fault_id,
        primary_fault_key=fault_key,
        primary_fault_name=fault_name,
        status=diag.status,
        severity=diag.severity,
        confidence_score=diag.confidence_score,
        summary=diag.summary,
        diagnostic_policy_version=diag.diagnostic_policy_version,
        generated_at=diag.generated_at,
        reviewed_by=diag.reviewed_by,
        reviewed_at=diag.reviewed_at,
        review_note=diag.review_note,
        review_status=diag.review_status,
        evidence_items=ev_items,
    )


def run_diagnosis(
    db: Session,
    *,
    actor: User,
    equipment_id: uuid.UUID | str,
    window_size: int = 12,
) -> DiagnosisResponse:
    """Orchestrate hybrid diagnostic reasoning across Rules, ML, and Knowledge Graph."""
    equipment = eq_service.get_equipment(db, actor, equipment_id)

    if not _is_platform_admin(actor) and not has_permission(
        actor, Permission.DIAGNOSIS_GENERATE, organization_id=equipment.organization_id
    ):
        raise AppError("Permission denied to generate diagnoses.", code="FORBIDDEN", status_code=403)

    repository.ensure_default_faults(db, equipment.equipment_type_id)

    readings = reading_repo.list_readings(db, equipment_id=equipment.id, limit=window_size)
    # Order ascending for chronological window analysis
    readings = list(reversed(readings))

    # Case A: Insufficient data (< 2 readings)
    if len(readings) < 2:
        diag = repository.create_diagnosis(
            db,
            organization_id=equipment.organization_id,
            equipment_id=equipment.id,
            status=DiagnosisStatus.INSUFFICIENT_DATA.value,
            severity=Severity.LOW.value,
            confidence_score=0.1,
            summary="Insufficient telemetry observations to derive feature windows and evaluate rules.",
        )
        repository.add_evidence(
            db,
            diagnosis_id=diag.id,
            evidence_type=EvidenceType.SENSOR.value,
            details_json={
                "samples_available": len(readings),
                "samples_required": 2,
                "note": "A minimum of 2 telemetry samples are needed to evaluate trends.",
            },
        )
        db.commit()
        db.refresh(diag)
        return _build_diagnosis_response(diag)

    # -----------------------------------------------------------------------
    # Step 1: Rule Engine Evaluation
    # -----------------------------------------------------------------------
    latest = readings[-1]
    symptom_keys: list[str] = []
    rule_evidence: dict[str, Any] = {"active_breaches": []}
    rule_severity = Severity.LOW

    # Check active equipment monitoring rules
    active_rules = rule_repo.get_active_rules_for_equipment(
        db,
        organization_id=equipment.organization_id,
        equipment_type_id=equipment.equipment_type_id,
    )
    for rule in active_rules:
        val = None
        if rule.measurement_type == "temperature":
            val = latest.temperature_c
        elif rule.measurement_type == "vibration":
            val = latest.vibration_value
        elif rule.measurement_type == "speed":
            val = latest.speed_rpm
        elif rule.measurement_type == "load":
            val = latest.load_percent

        if val is not None:
            breached = False
            if rule.operator == "gt" and val > rule.threshold:
                breached = True
            elif rule.operator == "gte" and val >= rule.threshold:
                breached = True

            if breached:
                rule_evidence["active_breaches"].append(
                    {
                        "rule_id": str(rule.id),
                        "name": rule.name,
                        "metric": rule.measurement_type,
                        "value": val,
                        "threshold": rule.threshold,
                        "severity": rule.severity,
                    }
                )
                if rule.measurement_type == "temperature":
                    symptom_keys.append("sym_high_temperature")
                elif rule.measurement_type == "vibration":
                    symptom_keys.append("sym_high_vibration")

    # Fallback symptom extraction from raw physical thresholds
    if (latest.temperature_c or 0) > 70.0 and "sym_high_temperature" not in symptom_keys:
        symptom_keys.append("sym_high_temperature")
        rule_evidence["active_breaches"].append({"metric": "temperature_c", "value": latest.temperature_c, "threshold": 70.0})
    if (latest.vibration_value or 0) > 0.40 and "sym_high_vibration" not in symptom_keys:
        symptom_keys.append("sym_high_vibration")
        rule_evidence["active_breaches"].append({"metric": "vibration_value", "value": latest.vibration_value, "threshold": 0.40})

    if rule_evidence["active_breaches"]:
        rule_severity = Severity.HIGH if any(b.get("severity") in ("high", "critical") for b in rule_evidence["active_breaches"]) else Severity.MEDIUM

    # -----------------------------------------------------------------------
    # Step 2: Machine Learning Inference
    # -----------------------------------------------------------------------
    raw_window_dicts = [
        {
            "temperature_c": r.temperature_c or 50.0,
            "vibration_value": r.vibration_value or 0.05,
            "speed_rpm": r.speed_rpm or 1480.0,
            "load_percent": r.load_percent or 70.0,
            "timestamp": r.timestamp,
        }
        for r in readings
    ]
    features = build_features(raw_window_dicts)
    ml_bundle = _get_or_create_ml_model_bundle()
    ml_pred = predict_window(ml_bundle, features, minimum_confidence=0.55)

    # -----------------------------------------------------------------------
    # Step 3: Knowledge Graph Reasoning
    # -----------------------------------------------------------------------
    kg_engine = KnowledgeGraphEngine()
    kg_engine.load_from_db(db)

    # If DB graph is currently unpopulated, seed default motor graph nodes and edges
    if len(kg_engine.graph.nodes) == 0:
        from app.modules.knowledge_graph import service as kg_service
        kg_service.ensure_default_motor_knowledge_graph(db)
        kg_engine.load_from_db(db)

    graph_candidates = kg_engine.reason_from_symptoms_and_ml(
        symptom_keys=symptom_keys,
        ml_prediction_class=ml_pred["raw_predicted_class"],
    )

    # -----------------------------------------------------------------------
    # Step 4: Hybrid Combination & Arbitration (Policy v1.0)
    # -----------------------------------------------------------------------
    pred_class = ml_pred["predicted_class"]
    confidence = ml_pred["confidence"]

    # Healthy Motor path
    if not symptom_keys and pred_class == "normal" and confidence >= 0.70:
        status = DiagnosisStatus.NORMAL.value
        severity = Severity.LOW.value
        overall_confidence = 0.95
        summary = "Normal operating condition. Telemetry rules and ML inference indicate healthy motor operation."
        primary_fault = None
    else:
        # Faulty or Abnormal Motor path
        status = DiagnosisStatus.POSSIBLE_FAULT.value
        top_candidate = graph_candidates[0] if graph_candidates else None

        # Resolve primary fault entity
        fault_key_target = "stator_overheat" if "temperature" in str(symptom_keys) or pred_class == "overheating" else "bearing_wear"
        if top_candidate:
            fault_node_key = top_candidate["fault_key"]
            if "bearing" in fault_node_key:
                fault_key_target = "bearing_wear"
            elif "stator" in fault_node_key or "cooling" in fault_node_key:
                fault_key_target = "stator_overheat"

        primary_fault = repository.get_fault_by_key(db, fault_key_target)
        fault_name = primary_fault.name if primary_fault else "Mechanical / Thermal Abnormality"

        # Calculate combined confidence
        rule_conf = 0.9 if rule_evidence["active_breaches"] else 0.5
        overall_confidence = round(0.4 * rule_conf + 0.4 * confidence + 0.2 * (top_candidate["graph_score"] if top_candidate else 0.5), 3)
        overall_confidence = min(0.98, max(0.51, overall_confidence))

        severity = Severity.CRITICAL.value if (rule_severity == Severity.HIGH or "critical" in str(ml_pred)) else Severity.HIGH.value

        summary = (
            f"Advisory diagnosis: Probable {fault_name}. "
            f"Observed symptoms: {', '.join(symptom_keys) or 'Abnormal feature pattern'}. "
            f"ML prediction: {pred_class} (confidence: {confidence:.2f}). Verification recommended."
        )

    # Persist Diagnosis
    diag = repository.create_diagnosis(
        db,
        organization_id=equipment.organization_id,
        equipment_id=equipment.id,
        primary_fault_id=primary_fault.id if primary_fault else None,
        status=status,
        severity=severity,
        confidence_score=overall_confidence,
        summary=summary,
        diagnostic_policy_version="1.0",
    )

    # Persist Evidence 1: Rules
    repository.add_evidence(
        db,
        diagnosis_id=diag.id,
        evidence_type=EvidenceType.RULE.value,
        source_reference="monitoring_rules_engine",
        weight=0.4,
        details_json={
            "symptoms_identified": symptom_keys,
            "rule_breaches": rule_evidence["active_breaches"],
            "evaluation_timestamp": latest.timestamp.isoformat(),
        },
    )

    # Persist Evidence 2: Machine Learning
    repository.add_evidence(
        db,
        diagnosis_id=diag.id,
        evidence_type=EvidenceType.PREDICTION.value,
        source_reference=f"ml_model_{ml_bundle.get('version', '1.0.0')}",
        weight=0.4,
        details_json={
            "model_version": ml_bundle.get("version", "1.0.0"),
            "predicted_class": ml_pred["predicted_class"],
            "confidence": ml_pred["confidence"],
            "probabilities": ml_pred["probabilities"],
            "is_uncertain": ml_pred["is_uncertain"],
            "feature_summary": {k: round(float(v), 3) for k, v in list(features.items())[:6]},
        },
    )

    # Persist Evidence 3: Knowledge Graph
    repository.add_evidence(
        db,
        diagnosis_id=diag.id,
        evidence_type=EvidenceType.GRAPH.value,
        source_reference="knowledge_graph_engine",
        weight=0.2,
        details_json={
            "candidate_faults": graph_candidates[:3],
            "recommended_checks": graph_candidates[0]["diagnostic_steps"] if graph_candidates else [],
            "recommended_repairs": graph_candidates[0]["repair_actions"] if graph_candidates else [],
        },
    )

    audit_service.record_event(
        db,
        action=AuditAction.DIAGNOSIS_GENERATED,
        resource_type="diagnosis",
        resource_id=diag.id,
        actor_user_id=actor.id,
        organization_id=equipment.organization_id,
        metadata={"equipment_id": str(equipment.id), "status": status, "fault": primary_fault.key if primary_fault else None},
    )

    db.commit()
    db.refresh(diag)
    return _build_diagnosis_response(diag)


def review_diagnosis(
    db: Session,
    *,
    actor: User,
    diagnosis_id: uuid.UUID | str,
    payload: DiagnosisReviewRequest,
) -> DiagnosisResponse:
    diag = repository.get_diagnosis_by_id(db, diagnosis_id)
    if not diag:
        raise AppError("Diagnosis not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == diag.organization_id for m in memberships):
            raise AppError("Access denied to this diagnosis.", code="FORBIDDEN", status_code=403)
        if not has_permission(actor, Permission.DIAGNOSIS_REVIEW, organization_id=diag.organization_id):
            raise AppError("Permission denied to review diagnoses.", code="FORBIDDEN", status_code=403)

    updated = repository.record_review(
        db,
        diagnosis_id=diag.id,
        reviewer_id=actor.id,
        review_status=payload.review_status,
        review_note=payload.review_note,
    )

    audit_service.record_event(
        db,
        action=AuditAction.DIAGNOSIS_REVIEWED,
        resource_type="diagnosis",
        resource_id=diag.id,
        actor_user_id=actor.id,
        organization_id=diag.organization_id,
        metadata={"decision": payload.review_status, "note": payload.review_note},
    )

    db.commit()
    db.refresh(updated)
    return _build_diagnosis_response(updated)


def get_diagnosis(
    db: Session,
    *,
    actor: User,
    diagnosis_id: uuid.UUID | str,
) -> DiagnosisResponse:
    diag = repository.get_diagnosis_by_id(db, diagnosis_id)
    if not diag:
        raise AppError("Diagnosis not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == diag.organization_id for m in memberships):
            raise AppError("Access denied to this diagnosis.", code="FORBIDDEN", status_code=403)

    return _build_diagnosis_response(diag)


def list_diagnoses(
    db: Session,
    *,
    actor: User,
    organization_id: uuid.UUID | str | None = None,
    equipment_id: uuid.UUID | str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[DiagnosisResponse]:
    target_org_id = None
    if organization_id:
        target_org_id = eq_service.resolve_organization_for_actor(actor, organization_id)
    elif not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if memberships:
            target_org_id = memberships[0].organization_id

    eid = None
    if equipment_id:
        eq = eq_service.get_equipment(db, actor, equipment_id)
        eid = eq.id

    diagnoses = repository.list_diagnoses(
        db,
        organization_id=target_org_id,
        equipment_id=eid,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [_build_diagnosis_response(d) for d in diagnoses]

