"""Phase 5 — Hybrid Diagnostics Test Suite.

Covers:
- Feature extraction and contract validation
- Scikit-learn Random Forest baseline training and artifact versioning
- Inference contract with uncertainty handling and advisory disclaimer
- NetworkX Knowledge Graph symptom-to-fault traversal, components, checks, and repairs
- Hybrid Diagnostic Orchestrator (Rules + ML + Knowledge Graph)
- Simulated fault scenario diagnostic evaluations (healthy, overheating, bearing wear)
- Insufficient data edge cases
- Human review workflow (confirmed_by_reviewer, dismissed, review notes)
- Multi-tenant isolation and role-based permissions
- Advisory disclaimer verification (no physical fault claims)
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
import sys
import uuid

import pytest
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.core.config import settings
from app.ml.baseline_model import (
    generate_training_windows,
    predict_window,
    train_baseline_classifier,
)
from app.ml.features import (
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
    build_features,
    to_feature_vector,
)
from app.models import UserStatus
from app.models.enums import DiagnosisStatus, EvidenceType, NodeType, RelationshipType, ReviewStatus
from app.modules.auth import service as auth_service
from app.modules.diagnostics import repository as diag_repo
from app.modules.diagnostics import service as diag_service
from app.modules.equipment import repository as eq_repo
from app.modules.knowledge_graph.engine import KnowledgeGraphEngine
from app.modules.knowledge_graph import service as kg_service
from app.modules.monitoring import repository as rule_repo
from app.modules.organizations import service as org_service
from app.modules.sensors import reading_repository as reading_repo
from app.modules.sensors import repository as sensor_repo
from simulator.motor.generator import ReadingGenerator
from simulator.scenarios.bearing_wear import perturbation as bearing_wear_pert
from simulator.scenarios.normal import perturbation as normal_pert
from simulator.scenarios.overheating import perturbation as overheating_pert

PASSWORD = "test-pass-phase5"
ADMIN_PASSWORD = "admin-pass-phase5"


# ---------------------------------------------------------------------------
# Test Context Helpers
# ---------------------------------------------------------------------------


def _headers(csrf_token: str | None) -> dict[str, str]:
    if not csrf_token:
        return {}
    return {settings.csrf_header_name: csrf_token}


def _login(client: TestClient, email: str, password: str = PASSWORD) -> tuple[int, dict, str | None]:
    response = client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": email, "password": password},
    )
    csrf_token = client.cookies.get(settings.csrf_cookie_name)
    return response.status_code, response.json(), csrf_token


def _setup_diagnostics_context(db):
    auth_service.repository.ensure_default_roles_and_permissions(db)
    eq_types = eq_repo.ensure_default_equipment_types(db)
    motor_type = eq_types["electric_motor"]

    admin = auth_service.repository.get_user_by_email(db, "diag_admin@example.com")
    if not admin:
        admin = auth_service.create_user(
            db,
            name="Diagnostics Admin",
            email="diag_admin@example.com",
            password=ADMIN_PASSWORD,
            role="platform_admin",
            status=UserStatus.ACTIVE.value,
        )

    # Org A
    org_a = org_service.get_organization_by_slug(db, "diag-plant-a")
    if not org_a:
        org_a = org_service.create_organization(
            db,
            actor=admin,
            name="Diagnostics Plant A",
            slug="diag-plant-a",
        )

    maintainer_a = auth_service.repository.get_user_by_email(db, "maint_a@example.com")
    if not maintainer_a:
        maintainer_a = auth_service.create_user(
            db,
            name="Maintainer A",
            email="maint_a@example.com",
            password=PASSWORD,
            role="maintainer",
            organization_id=org_a.id,
            status=UserStatus.ACTIVE.value,
        )
        org_service.add_member(db, actor=admin, organization_id=org_a.id, user_id=maintainer_a.id)

    viewer_a = auth_service.repository.get_user_by_email(db, "viewer_a@example.com")
    if not viewer_a:
        viewer_a = auth_service.create_user(
            db,
            name="Viewer A",
            email="viewer_a@example.com",
            password=PASSWORD,
            role="demo_user",
            organization_id=org_a.id,
            status=UserStatus.ACTIVE.value,
        )
        org_service.add_member(db, actor=admin, organization_id=org_a.id, user_id=viewer_a.id)

    # Org B (for cross-tenant checks)
    org_b = org_service.get_organization_by_slug(db, "diag-plant-b")
    if not org_b:
        org_b = org_service.create_organization(
            db,
            actor=admin,
            name="Diagnostics Plant B",
            slug="diag-plant-b",
        )

    maintainer_b = auth_service.repository.get_user_by_email(db, "maint_b@example.com")
    if not maintainer_b:
        maintainer_b = auth_service.create_user(
            db,
            name="Maintainer B",
            email="maint_b@example.com",
            password=PASSWORD,
            role="maintainer",
            organization_id=org_b.id,
            status=UserStatus.ACTIVE.value,
        )
        org_service.add_member(db, actor=admin, organization_id=org_b.id, user_id=maintainer_b.id)

    # Equipment A
    eq_a = db.query(eq_repo.Equipment).filter_by(organization_id=org_a.id, asset_tag="TEST-DIAG-01").first()
    if not eq_a:
        eq_a = eq_repo.create_equipment(
            db,
            organization_id=org_a.id,
            equipment_type_id=motor_type.id,
            name="Induction Motor Plant A",
            created_by=admin.id,
            asset_tag="TEST-DIAG-01",
            status="operational",
        )

    # Add components and sensors to Equipment A
    comp_bearing = db.query(eq_repo.Component).filter_by(equipment_id=eq_a.id, component_key="bearing_front").first()
    if not comp_bearing:
        comp_bearing = eq_repo.create_component(
            db,
            organization_id=org_a.id,
            equipment_id=eq_a.id,
            component_key="bearing_front",
            name="Drive-End Bearing",
            component_type="bearing",
        )

    comp_stator = db.query(eq_repo.Component).filter_by(equipment_id=eq_a.id, component_key="stator").first()
    if not comp_stator:
        comp_stator = eq_repo.create_component(
            db,
            organization_id=org_a.id,
            equipment_id=eq_a.id,
            component_key="stator",
            name="Stator Windings",
            component_type="stator",
        )

    s_temp = db.query(sensor_repo.Sensor).filter_by(equipment_id=eq_a.id, sensor_key="temp_stator").first()
    if not s_temp:
        s_temp = sensor_repo.create_sensor(
            db,
            organization_id=org_a.id,
            equipment_id=eq_a.id,
            component_id=comp_stator.id,
            sensor_key="temp_stator",
            measurement_type="temperature",
            unit="°C",
        )

    s_vib = db.query(sensor_repo.Sensor).filter_by(equipment_id=eq_a.id, sensor_key="vib_bearing_front").first()
    if not s_vib:
        s_vib = sensor_repo.create_sensor(
            db,
            organization_id=org_a.id,
            equipment_id=eq_a.id,
            component_id=comp_bearing.id,
            sensor_key="vib_bearing_front",
            measurement_type="vibration",
            unit="mm/s",
        )

    # Rules for Org A
    existing_rule_temp = db.query(rule_repo.MonitoringRule).filter_by(
        organization_id=org_a.id, measurement_type="temperature"
    ).first()
    if not existing_rule_temp:
        rule_repo.create_rule(
            db,
            organization_id=org_a.id,
            equipment_type_id=motor_type.id,
            name="High Stator Temperature Rule",
            measurement_type="temperature",
            operator="gt",
            threshold=75.0,
            unit="°C",
            severity="high",
            created_by=admin.id,
        )

    existing_rule_vib = db.query(rule_repo.MonitoringRule).filter_by(
        organization_id=org_a.id, measurement_type="vibration"
    ).first()
    if not existing_rule_vib:
        rule_repo.create_rule(
            db,
            organization_id=org_a.id,
            equipment_type_id=motor_type.id,
            name="High Vibration Rule",
            measurement_type="vibration",
            operator="gt",
            threshold=0.5,
            unit="mm/s",
            severity="critical",
            created_by=admin.id,
        )

    # Seed baseline faults & knowledge graph
    diag_repo.ensure_default_faults(db, motor_type.id)
    kg_service.ensure_default_motor_knowledge_graph(db)

    db.commit()

    return {
        "admin": admin,
        "org_a": org_a,
        "maintainer_a": maintainer_a,
        "viewer_a": viewer_a,
        "org_b": org_b,
        "maintainer_b": maintainer_b,
        "motor_a": eq_a,
        "sensor_temp": s_temp,
        "sensor_vib": s_vib,
        "motor_type": motor_type,
    }


# ---------------------------------------------------------------------------
# ML Training & Inference Contract Unit Tests
# ---------------------------------------------------------------------------


def test_feature_extraction_contract():
    """Verify feature extractor extracts all defined features with correct types and keys."""
    gen = ReadingGenerator(
        equipment_id="motor-feat-test",
        scenario_id="normal",
        scenario_label="normal",
        seed=42,
    )
    raw = list(gen.stream(perturbation_fn=normal_pert, max_steps=15))
    feats = build_features(raw)

    assert isinstance(feats, dict)
    assert set(feats.keys()) == set(FEATURE_NAMES)
    for name in FEATURE_NAMES:
        assert isinstance(feats[name], float)

    vec = to_feature_vector(feats)
    assert len(vec) == len(FEATURE_NAMES)
    assert all(isinstance(v, float) for v in vec)


def test_train_baseline_classifier_and_metrics(tmp_path, monkeypatch):
    """Verify that training baseline classifier produces valid artifact bundle and high accuracy."""
    monkeypatch.setattr("app.ml.service.models_root", lambda: tmp_path)

    clf, metrics, artifact_path = train_baseline_classifier(
        train_seeds=[10, 20],
        test_seeds=[30],
        n_estimators=15,
        random_state=42,
    )

    assert artifact_path.exists()
    assert metrics["accuracy"] >= 0.80
    assert metrics["macro_f1"] >= 0.80
    assert "classification_report" in metrics


def test_predict_window_contract_and_uncertainty():
    """Verify prediction contract output format, probabilities map, and uncertainty thresholding."""
    gen_hot = ReadingGenerator(
        equipment_id="motor-hot",
        scenario_id="overheating",
        scenario_label="overheating",
        seed=55,
    )
    hot_readings = list(gen_hot.stream(perturbation_fn=overheating_pert, max_steps=20))
    feats = build_features(hot_readings)

    # Train a quick model
    clf, _, _ = train_baseline_classifier(train_seeds=[1, 2], test_seeds=[3], n_estimators=10)
    bundle = {
        "model": clf,
        "labels": clf.classes_,
        "version": "1.0.0",
    }

    pred = predict_window(bundle, feats, minimum_confidence=0.40)
    assert "predicted_class" in pred
    assert "confidence" in pred
    assert "probabilities" in pred
    assert "disclaimer" in pred
    assert "Advisory" in pred["disclaimer"]
    assert pred["predicted_class"] == "overheating"

    # Test uncertainty threshold triggering
    pred_uncertain = predict_window(bundle, feats, minimum_confidence=0.9999)
    assert pred_uncertain["is_uncertain"] is True
    assert pred_uncertain["predicted_class"] == "uncertain"
    assert pred_uncertain["raw_predicted_class"] == "overheating"


# ---------------------------------------------------------------------------
# NetworkX Knowledge Graph Reasoning Tests
# ---------------------------------------------------------------------------


def test_knowledge_graph_engine_reasoning(db):
    """Verify KnowledgeGraphEngine correctly traverses symptoms and ML classes to infer faults and repairs."""
    kg_service.ensure_default_motor_knowledge_graph(db)
    engine = KnowledgeGraphEngine.from_db(db)

    assert engine.graph.number_of_nodes() >= 10
    assert engine.graph.number_of_edges() >= 10

    # Test 1: Temperature symptom + overheating prediction -> stator_overheat fault
    res = engine.reason_from_symptoms_and_ml(
        symptoms=["sym_high_temperature"],
        ml_predicted_class="overheating",
        ml_confidence=0.92,
    )

    assert res["inferred_fault_key"] == "stator_overheat"
    assert res["confidence"] >= 0.85
    assert len(res["affected_components"]) >= 1
    assert any("stator" in c["label"].lower() for c in res["affected_components"])
    assert any("thermal" in p["label"].lower() for p in res["diagnostic_procedures"])

    # Test 2: Vibration symptom + bearing_abnormality prediction -> bearing_wear fault
    res_vib = engine.reason_from_symptoms_and_ml(
        symptoms=["sym_high_vibration"],
        ml_predicted_class="bearing_abnormality",
        ml_confidence=0.95,
    )

    assert res_vib["inferred_fault_key"] == "bearing_wear"
    assert res_vib["confidence"] >= 0.85
    assert any("bearing" in c["label"].lower() for c in res_vib["affected_components"])
    assert any("fft" in p["label"].lower() for p in res_vib["diagnostic_procedures"])
    assert any("bearing" in r["label"].lower() for r in res_vib["repair_actions"])

    # Test 3: Normal / empty input -> no fault inferred
    res_normal = engine.reason_from_symptoms_and_ml(
        symptoms=[],
        ml_predicted_class="normal",
        ml_confidence=0.98,
    )
    assert res_normal["inferred_fault_key"] is None
    assert res_normal["confidence"] >= 0.90


def test_knowledge_graph_neighborhood(db):
    """Verify neighborhood retrieval returns ego network with proper depth limiting."""
    kg_service.ensure_default_motor_knowledge_graph(db)
    engine = KnowledgeGraphEngine.from_db(db)

    nb = engine.get_neighborhood("fault_bearing_wear", depth=1)
    assert nb["center_node"]["key"] == "fault_bearing_wear"
    assert len(nb["nodes"]) >= 3
    assert len(nb["edges"]) >= 3


# ---------------------------------------------------------------------------
# Hybrid Diagnostic Orchestrator Tests
# ---------------------------------------------------------------------------


def test_diagnostic_orchestrator_normal(db):
    """Verify that a healthy motor window results in normal diagnosis with 3 evidence items."""
    ctx = _setup_diagnostics_context(db)
    eq = ctx["motor_a"]
    s_temp = ctx["sensor_temp"]
    s_vib = ctx["sensor_vib"]
    maint = ctx["maintainer_a"]

    # Ingest 15 normal readings
    base_time = datetime.now(UTC) - timedelta(minutes=5)
    for i in range(15):
        t = base_time + timedelta(seconds=i * 2)
        reading_repo.insert_reading(
            db,
            sensor_id=s_temp.id,
            equipment_id=eq.id,
            timestamp=t,
            value=45.0 + (i % 3) * 0.5,
        )
        reading_repo.insert_reading(
            db,
            sensor_id=s_vib.id,
            equipment_id=eq.id,
            timestamp=t,
            value=0.15 + (i % 2) * 0.02,
        )
    db.commit()

    resp = diag_service.run_diagnosis(db, actor=maint, equipment_id=eq.id, window_size=12)

    assert resp.status == DiagnosisStatus.NORMAL.value
    assert resp.primary_fault_id is None
    assert resp.confidence_score >= 0.80
    assert "normal" in resp.summary.lower()
    assert len(resp.evidence_items) == 3

    # Check evidence types
    ev_types = {e.evidence_type for e in resp.evidence_items}
    assert ev_types == {EvidenceType.RULE.value, EvidenceType.PREDICTION.value, EvidenceType.GRAPH.value}


def test_diagnostic_orchestrator_overheating(db):
    """Verify that an overheating motor window triggers rules, ML class, and knowledge graph."""
    ctx = _setup_diagnostics_context(db)
    eq = ctx["motor_a"]
    s_temp = ctx["sensor_temp"]
    s_vib = ctx["sensor_vib"]
    maint = ctx["maintainer_a"]

    # Ingest 15 overheating readings (temp 95°C > 75°C threshold)
    base_time = datetime.now(UTC) - timedelta(minutes=2)
    for i in range(15):
        t = base_time + timedelta(seconds=i * 2)
        reading_repo.insert_reading(
            db,
            sensor_id=s_temp.id,
            equipment_id=eq.id,
            timestamp=t,
            value=95.0 + i * 0.8,
        )
        reading_repo.insert_reading(
            db,
            sensor_id=s_vib.id,
            equipment_id=eq.id,
            timestamp=t,
            value=0.20,
        )
    db.commit()

    resp = diag_service.run_diagnosis(db, actor=maint, equipment_id=eq.id, window_size=12)

    assert resp.status == DiagnosisStatus.POSSIBLE_FAULT.value
    assert resp.primary_fault_key == "stator_overheat"
    assert resp.severity in ["high", "critical"]
    assert resp.confidence_score >= 0.80
    assert "stator" in resp.summary.lower()
    assert len(resp.evidence_items) == 3

    # Check details of each evidence item
    rule_ev = next(e for e in resp.evidence_items if e.evidence_type == EvidenceType.RULE.value)
    assert len(rule_ev.details_json["violations"]) >= 1
    assert "sym_high_temperature" in rule_ev.details_json["symptoms"]

    pred_ev = next(e for e in resp.evidence_items if e.evidence_type == EvidenceType.PREDICTION.value)
    assert pred_ev.details_json["predicted_class"] == "overheating"

    graph_ev = next(e for e in resp.evidence_items if e.evidence_type == EvidenceType.GRAPH.value)
    assert graph_ev.details_json["inferred_fault_key"] == "stator_overheat"
    assert len(graph_ev.details_json["affected_components"]) >= 1


def test_diagnostic_orchestrator_bearing_wear(db):
    """Verify that a high vibration motor window triggers bearing wear diagnosis and recommended procedures."""
    ctx = _setup_diagnostics_context(db)
    eq = ctx["motor_a"]
    s_temp = ctx["sensor_temp"]
    s_vib = ctx["sensor_vib"]
    maint = ctx["maintainer_a"]

    # Ingest 15 bearing degradation readings (vibration 1.8 mm/s > 0.5 mm/s threshold)
    base_time = datetime.now(UTC) - timedelta(minutes=1)
    for i in range(15):
        t = base_time + timedelta(seconds=i * 2)
        reading_repo.insert_reading(
            db,
            sensor_id=s_temp.id,
            equipment_id=eq.id,
            timestamp=t,
            value=52.0,
        )
        reading_repo.insert_reading(
            db,
            sensor_id=s_vib.id,
            equipment_id=eq.id,
            timestamp=t,
            value=1.85 + (i % 3) * 0.1,
        )
    db.commit()

    resp = diag_service.run_diagnosis(db, actor=maint, equipment_id=eq.id, window_size=12)

    assert resp.status == DiagnosisStatus.POSSIBLE_FAULT.value
    assert resp.primary_fault_key == "bearing_wear"
    assert resp.confidence_score >= 0.80
    assert len(resp.evidence_items) == 3

    graph_ev = next(e for e in resp.evidence_items if e.evidence_type == EvidenceType.GRAPH.value)
    assert any("bearing" in p["label"].lower() or "fft" in p["label"].lower() for p in graph_ev.details_json["diagnostic_procedures"])
    assert any("bearing" in r["label"].lower() or "lubricat" in r["label"].lower() for r in graph_ev.details_json["repair_actions"])


def test_diagnostic_orchestrator_insufficient_data(db):
    """Verify that attempting diagnosis with < 2 readings produces INSUFFICIENT_DATA status gracefully."""
    ctx = _setup_diagnostics_context(db)
    # Create empty equipment
    empty_motor = eq_repo.create_equipment(
        db,
        organization_id=ctx["org_a"].id,
        equipment_type_id=ctx["motor_type"].id,
        name="Empty Untracked Motor",
        created_by=ctx["admin"].id,
        asset_tag="TEST-EMPTY-01",
        status="operational",
    )
    db.commit()

    resp = diag_service.run_diagnosis(db, actor=ctx["maintainer_a"], equipment_id=empty_motor.id)
    assert resp.status == DiagnosisStatus.INSUFFICIENT_DATA.value
    assert resp.confidence_score == 0.0
    assert "insufficient telemetry" in resp.summary.lower()


# ---------------------------------------------------------------------------
# API Endpoints & Human Review Tests
# ---------------------------------------------------------------------------


def test_diagnoses_api_lifecycle_and_review(client: TestClient, db):
    """Verify HTTP API: POST generate, GET list, GET detail, POST review, and audit logging."""
    ctx = _setup_diagnostics_context(db)
    maint = ctx["maintainer_a"]
    eq = ctx["motor_a"]
    s_temp = ctx["sensor_temp"]

    # Seed fresh readings
    base_time = datetime.now(UTC) - timedelta(minutes=1)
    for i in range(12):
        reading_repo.insert_reading(
            db,
            sensor_id=s_temp.id,
            equipment_id=eq.id,
            timestamp=base_time + timedelta(seconds=i * 2),
            value=88.0,
        )
    db.commit()

    # Login as Maintainer A
    status, body, csrf = _login(client, maint.email, PASSWORD)
    assert status == 200

    # 1. Generate Diagnosis via API
    gen_resp = client.post(
        f"{settings.api_v1_prefix}/diagnoses/generate",
        json={"equipment_id": str(eq.id), "window_size": 12},
        headers=_headers(csrf),
    )
    assert gen_resp.status_code == 201
    diag_data = gen_resp.json()
    diag_id = diag_data["id"]
    assert diag_data["status"] == DiagnosisStatus.POSSIBLE_FAULT.value
    assert diag_data["primary_fault_key"] == "stator_overheat"
    assert len(diag_data["evidence_items"]) == 3
    assert diag_data["review_status"] == ReviewStatus.PENDING.value

    # 2. List Diagnoses
    list_resp = client.get(
        f"{settings.api_v1_prefix}/diagnoses?equipment_id={eq.id}",
        headers=_headers(csrf),
    )
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1
    assert any(d["id"] == diag_id for d in items)

    # 3. Get Diagnosis Detail
    detail_resp = client.get(
        f"{settings.api_v1_prefix}/diagnoses/{diag_id}",
        headers=_headers(csrf),
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == diag_id

    # 4. Human Review -> Confirmed
    review_resp = client.post(
        f"{settings.api_v1_prefix}/diagnoses/{diag_id}/review",
        json={
            "review_status": "confirmed_by_reviewer",
            "review_note": "Physical inspection confirmed stator coil discolouration and thermal distress.",
        },
        headers=_headers(csrf),
    )
    assert review_resp.status_code == 200
    rev_data = review_resp.json()
    assert rev_data["review_status"] == "confirmed_by_reviewer"
    assert rev_data["reviewed_by"] == str(maint.id)
    assert "discolouration" in rev_data["review_note"]

    # 5. Verify persistence in DB
    db_diag = diag_repo.get_diagnosis_by_id(db, uuid.UUID(diag_id))
    assert db_diag.review_status == "confirmed_by_reviewer"


def test_diagnoses_api_review_dismiss(client: TestClient, db):
    """Verify that a reviewer can dismiss a false positive diagnosis."""
    ctx = _setup_diagnostics_context(db)
    maint = ctx["maintainer_a"]
    eq = ctx["motor_a"]

    # Generate a diagnosis directly
    diag = diag_repo.create_diagnosis(
        db,
        organization_id=ctx["org_a"].id,
        equipment_id=eq.id,
        status=DiagnosisStatus.POSSIBLE_FAULT.value,
        severity="medium",
        confidence_score=0.65,
        summary="Transient spike caused advisory warning.",
    )
    db.commit()

    # Login as Maintainer A
    _, _, csrf = _login(client, maint.email, PASSWORD)

    # Dismiss diagnosis
    resp = client.post(
        f"{settings.api_v1_prefix}/diagnoses/{diag.id}/review",
        json={
            "review_status": "dismissed",
            "review_note": "Spike caused by ambient welding activity nearby, motor confirmed operational.",
        },
        headers=_headers(csrf),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["review_status"] == "dismissed"
    assert data["status"] == DiagnosisStatus.DISMISSED.value


# ---------------------------------------------------------------------------
# Multi-Tenant Isolation & Role Authorization Tests
# ---------------------------------------------------------------------------


def test_cross_tenant_isolation(client: TestClient, db):
    """Verify maintainer in Org B cannot view or review diagnosis of Org A."""
    ctx = _setup_diagnostics_context(db)
    maint_b = ctx["maintainer_b"]
    eq_a = ctx["motor_a"]

    # Create diagnosis in Org A
    diag = diag_repo.create_diagnosis(
        db,
        organization_id=ctx["org_a"].id,
        equipment_id=eq_a.id,
        status=DiagnosisStatus.POSSIBLE_FAULT.value,
        severity="high",
        confidence_score=0.88,
        summary="Confidential Org A fault diagnosis.",
    )
    db.commit()

    # Login as Maintainer B (Org B)
    status, _, csrf = _login(client, maint_b.email, PASSWORD)
    assert status == 200

    # Attempt to view Org A diagnosis -> 403 Forbidden or 404 Not Found
    get_resp = client.get(
        f"{settings.api_v1_prefix}/diagnoses/{diag.id}",
        headers=_headers(csrf),
    )
    assert get_resp.status_code in (403, 404)

    # Attempt to review Org A diagnosis -> 403 Forbidden or 404 Not Found
    rev_resp = client.post(
        f"{settings.api_v1_prefix}/diagnoses/{diag.id}/review",
        json={"review_status": "confirmed_by_reviewer", "review_note": "Unauthorized review attempt"},
        headers=_headers(csrf),
    )
    assert rev_resp.status_code in (403, 404)


def test_viewer_permission_restriction(client: TestClient, db):
    """Verify demo viewer role cannot generate or review diagnoses."""
    ctx = _setup_diagnostics_context(db)
    viewer = ctx["viewer_a"]
    eq = ctx["motor_a"]

    diag = diag_repo.create_diagnosis(
        db,
        organization_id=ctx["org_a"].id,
        equipment_id=eq.id,
        status=DiagnosisStatus.POSSIBLE_FAULT.value,
        severity="medium",
        confidence_score=0.70,
        summary="Advisory test diagnosis.",
    )
    db.commit()

    # Login as Viewer
    _, _, csrf = _login(client, viewer.email, PASSWORD)

    # Viewer can read diagnoses
    read_resp = client.get(
        f"{settings.api_v1_prefix}/diagnoses/{diag.id}",
        headers=_headers(csrf),
    )
    assert read_resp.status_code == 200

    # Viewer cannot generate diagnosis -> 403 Forbidden
    gen_resp = client.post(
        f"{settings.api_v1_prefix}/diagnoses/generate",
        json={"equipment_id": str(eq.id)},
        headers=_headers(csrf),
    )
    assert gen_resp.status_code == 403

    # Viewer cannot review diagnosis -> 403 Forbidden
    rev_resp = client.post(
        f"{settings.api_v1_prefix}/diagnoses/{diag.id}/review",
        json={"review_status": "confirmed_by_reviewer", "review_note": "Viewer cannot approve"},
        headers=_headers(csrf),
    )
    assert rev_resp.status_code == 403


def test_unauthenticated_request_rejected(client: TestClient, db):
    """Verify unauthenticated requests return 401."""
    resp = client.get(f"{settings.api_v1_prefix}/diagnoses")
    assert resp.status_code == 401
