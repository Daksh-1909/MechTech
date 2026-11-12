"""Repository for Diagnosis, DiagnosisEvidence, and Fault entities."""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.time import utcnow
from app.models.diagnosis import Diagnosis, DiagnosisEvidence
from app.models.enums import DiagnosisStatus, ModelStatus, ReviewStatus, Severity
from app.models.fault import Fault
from app.models.ml_model import MLModel


def ensure_default_faults(db: Session, equipment_type_id: uuid.UUID | None = None) -> dict[str, Fault]:
    default_faults = [
        ("bearing_wear", "Rolling Element Bearing Deterioration", "Fatigue wear, flaking, or lack of lubrication in drive-end bearing races.", "critical"),
        ("stator_overheat", "Stator Winding Overheating", "Excessive temperature rise in three-phase stator copper windings.", "high"),
        ("cooling_failure", "Cooling System Airflow Obstruction", "Clogged ventilation ribs or damaged bi-directional fan assembly.", "medium"),
        ("mechanical_imbalance", "Rotor Dynamic Imbalance", "Mass eccentricity or misalignment generating 1X rotational speed vibration.", "medium"),
    ]
    faults_map = {}
    for key, name, desc, sev in default_faults:
        f = db.scalar(select(Fault).where(Fault.key == key))
        if not f:
            f = Fault(
                key=key,
                name=name,
                description=desc,
                equipment_type_id=equipment_type_id,
                default_severity=sev,
            )
            db.add(f)
            db.flush()
        faults_map[key] = f
    db.flush()
    return faults_map


def get_fault_by_key(db: Session, key: str) -> Fault | None:
    return db.scalar(select(Fault).where(Fault.key == key))


def get_ml_model_by_key_version(db: Session, model_key: str, version: str) -> MLModel | None:
    return db.scalar(select(MLModel).where(MLModel.model_key == model_key, MLModel.version == version))


def ensure_default_ml_model(
    db: Session,
    *,
    model_key: str = "motor_fault_classifier",
    version: str = "1.0.0",
    artifact_path: str = "models/motor_fault_classifier_v1.joblib",
    feature_schema: dict[str, Any] | None = None,
    dataset_version: str = "v1.0-synthetic",
    metrics: dict[str, Any] | None = None,
    equipment_type_id: uuid.UUID | None = None,
) -> MLModel:
    entry = get_ml_model_by_key_version(db, model_key, version)
    if not entry:
        from app.ml.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION

        if feature_schema is None:
            feature_schema = {
                "schema_version": FEATURE_SCHEMA_VERSION,
                "features": list(FEATURE_NAMES),
            }
        entry = MLModel(
            model_key=model_key,
            version=version,
            equipment_type_id=equipment_type_id,
            artifact_path=artifact_path,
            feature_schema=feature_schema,
            dataset_version=dataset_version,
            metrics=metrics,
            status=ModelStatus.ACTIVE.value,
        )
        db.add(entry)
        db.flush()
    return entry


def create_diagnosis(
    db: Session,
    *,
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    status: str,
    severity: str,
    confidence_score: float,
    summary: str,
    diagnostic_policy_version: str = "1.0",
    primary_fault_id: uuid.UUID | None = None,
) -> Diagnosis:
    diag = Diagnosis(
        organization_id=organization_id,
        equipment_id=equipment_id,
        primary_fault_id=primary_fault_id,
        status=status,
        severity=severity,
        confidence_score=confidence_score,
        summary=summary,
        diagnostic_policy_version=diagnostic_policy_version,
        generated_at=utcnow(),
        review_status=ReviewStatus.PENDING.value,
    )
    db.add(diag)
    db.flush()
    return diag


def add_evidence(
    db: Session,
    *,
    diagnosis_id: uuid.UUID,
    evidence_type: str,
    details_json: dict[str, Any],
    source_reference: str | None = None,
    weight: float = 1.0,
) -> DiagnosisEvidence:
    evidence = DiagnosisEvidence(
        diagnosis_id=diagnosis_id,
        evidence_type=evidence_type,
        source_reference=source_reference,
        weight=weight,
        details_json=details_json,
        created_at=utcnow(),
    )
    db.add(evidence)
    db.flush()
    return evidence


def get_diagnosis_by_id(db: Session, diagnosis_id: uuid.UUID | str) -> Diagnosis | None:
    did = diagnosis_id if isinstance(diagnosis_id, uuid.UUID) else uuid.UUID(str(diagnosis_id))
    return db.scalar(
        select(Diagnosis)
        .options(
            joinedload(Diagnosis.primary_fault),
            joinedload(Diagnosis.evidence_items),
            joinedload(Diagnosis.reviewer),
            joinedload(Diagnosis.equipment),
        )
        .where(Diagnosis.id == did)
    )


def list_diagnoses(
    db: Session,
    *,
    organization_id: uuid.UUID | str | None = None,
    equipment_id: uuid.UUID | str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Diagnosis]:
    stmt = (
        select(Diagnosis)
        .options(
            joinedload(Diagnosis.primary_fault),
            joinedload(Diagnosis.evidence_items),
        )
        .order_by(Diagnosis.generated_at.desc(), Diagnosis.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if organization_id is not None:
        oid = organization_id if isinstance(organization_id, uuid.UUID) else uuid.UUID(str(organization_id))
        stmt = stmt.where(Diagnosis.organization_id == oid)
    if equipment_id is not None:
        eid = equipment_id if isinstance(equipment_id, uuid.UUID) else uuid.UUID(str(equipment_id))
        stmt = stmt.where(Diagnosis.equipment_id == eid)
    if status is not None:
        stmt = stmt.where(Diagnosis.status == status)

    return list(db.scalars(stmt))


def record_review(
    db: Session,
    *,
    diagnosis_id: uuid.UUID | str,
    reviewer_id: uuid.UUID,
    review_status: str,
    review_note: str | None = None,
) -> Diagnosis | None:
    diag = get_diagnosis_by_id(db, diagnosis_id)
    if not diag:
        return None

    diag.review_status = review_status
    if review_status == "confirmed_by_reviewer":
        diag.status = DiagnosisStatus.CONFIRMED_BY_REVIEWER.value
    elif review_status in ("dismissed", "rejected"):
        diag.status = DiagnosisStatus.DISMISSED.value

    diag.reviewed_by = reviewer_id
    diag.reviewed_at = utcnow()
    diag.review_note = review_note
    db.flush()
    return diag

