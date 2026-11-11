"""Phase 4 — Monitoring and Alerts Test Suite.

Covers:
- Monitoring rule creation, validation, update, and deletion
- Supported operators enforcement ('gt', 'gte', 'lt', 'lte', 'eq', 'neq')
- Threshold and duration evaluation engine
- Automatic anomaly event and alert generation on rule violations
- Alert lifecycle: open -> acknowledged -> resolved / dismissed
- Resolution notes and actor tracking
- Equipment health overview and staleness detection
- Cross-tenant rule and alert isolation
- Reproducible simulated fault scenario alert triggering (Roadmap Exit Criterion)
"""

import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.core.config import settings
from app.models import UserStatus
from app.models.enums import AlertStatus, RuleOperator, Severity
from app.modules.auth import service as auth_service
from app.modules.equipment import repository as eq_repo
from app.modules.organizations import service as org_service
from simulator.motor.generator import ReadingGenerator
from simulator.scenarios.overheating import perturbation as overheating_perturbation

PASSWORD = "test-pass-phase4"
ADMIN_PASSWORD = "admin-pass-phase4"


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


def _setup_monitoring_context(db):
    auth_service.repository.ensure_default_roles_and_permissions(db)
    eq_types = eq_repo.ensure_default_equipment_types(db)
    motor_type = eq_types["electric_motor"]

    admin = auth_service.repository.get_user_by_email(db, "mon_admin@example.com")
    if not admin:
        admin = auth_service.create_user(
            db,
            name="Monitoring Admin",
            email="mon_admin@example.com",
            password=ADMIN_PASSWORD,
            role="platform_admin",
            status=UserStatus.ACTIVE.value,
        )

    org_a = org_service.create_organization(db, actor=admin, name="Monitoring Org A", slug="mon-org-a")
    org_b = org_service.create_organization(db, actor=admin, name="Monitoring Org B", slug="mon-org-b")

    maintainer_a = auth_service.create_user(
        db,
        name="Maintainer A",
        email="mon.maintainer.a@example.com",
        password=PASSWORD,
        role="maintainer",
        organization_id=org_a.id,
    )
    maintainer_b = auth_service.create_user(
        db,
        name="Maintainer B",
        email="mon.maintainer.b@example.com",
        password=PASSWORD,
        role="maintainer",
        organization_id=org_b.id,
    )

    motor_a = eq_repo.create_equipment(
        db,
        organization_id=org_a.id,
        equipment_type_id=motor_type.id,
        name="Motor Alpha Line 1",
        created_by=admin.id,
        asset_tag="MON-MTR-A-01",
        specification={"rated_power_kw": 11.0, "rated_speed_rpm": 1475.0},
    )

    motor_b = eq_repo.create_equipment(
        db,
        organization_id=org_b.id,
        equipment_type_id=motor_type.id,
        name="Motor Beta Line 1",
        created_by=admin.id,
        asset_tag="MON-MTR-B-01",
        specification={"rated_power_kw": 15.0, "rated_speed_rpm": 1480.0},
    )

    db.commit()
    return admin, org_a, org_b, maintainer_a, maintainer_b, motor_a, motor_b, motor_type


def _reading(equipment_id: str, *, temp: float = 55.0, vib: float = 0.05, delta_s: int = 0) -> dict:
    ts = (datetime.now(UTC) - timedelta(seconds=delta_s)).isoformat()
    return {
        "equipment_id": equipment_id,
        "timestamp": ts,
        "temperature_c": temp,
        "vibration_value": vib,
        "vibration_unit": "simulated_index",
        "speed_rpm": 1475.0,
        "load_percent": 70.0,
        "source": "simulator",
        "source_event_id": f"event-{uuid.uuid4().hex[:12]}",
        "sequence_number": 0,
        "scenario_id": "normal",
        "scenario_label": "normal",
    }


# ---------------------------------------------------------------------------
# Monitoring Rules Tests
# ---------------------------------------------------------------------------


def test_create_and_get_monitoring_rule(client: TestClient, db_session) -> None:
    """Maintainer can create a threshold monitoring rule and retrieve it."""
    _, org_a, _, maintainer_a, _, motor_a, _, motor_type = _setup_monitoring_context(db_session)
    _, _, csrf = _login(client, maintainer_a.email)

    payload = {
        "organization_id": str(org_a.id),
        "equipment_type_id": str(motor_type.id),
        "name": "Stator Winding Overheat Warning",
        "measurement_type": "temperature",
        "operator": "gt",
        "threshold": 75.0,
        "unit": "°C",
        "duration_seconds": 0,
        "severity": "high",
        "is_enabled": True,
    }
    res = client.post(
        f"{settings.api_v1_prefix}/monitoring/rules",
        json=payload,
        headers=_headers(csrf),
    )
    assert res.status_code == 201, res.text
    rule = res.json()
    assert rule["name"] == "Stator Winding Overheat Warning"
    assert rule["threshold"] == 75.0
    assert rule["operator"] == "gt"
    assert rule["severity"] == "high"

    # GET /monitoring/rules/{id}
    res_get = client.get(
        f"{settings.api_v1_prefix}/monitoring/rules/{rule['id']}",
        headers=_headers(csrf),
    )
    assert res_get.status_code == 200
    assert res_get.json()["id"] == rule["id"]


def test_list_rules_tenant_isolation(client: TestClient, db_session) -> None:
    """Rules created in Org A are not visible to Maintainer of Org B."""
    _, org_a, org_b, maintainer_a, maintainer_b, _, _, _ = _setup_monitoring_context(db_session)
    _, _, csrf_a = _login(client, maintainer_a.email)
    _, _, csrf_b = _login(client, maintainer_b.email)

    # Create rule in Org A
    client.post(
        f"{settings.api_v1_prefix}/monitoring/rules",
        json={
            "organization_id": str(org_a.id),
            "name": "Org A Vibration Rule",
            "measurement_type": "vibration",
            "operator": "gt",
            "threshold": 0.5,
            "unit": "mm_s",
        },
        headers=_headers(csrf_a),
    )

    # Maintainer A sees it
    res_a = client.get(f"{settings.api_v1_prefix}/monitoring/rules", headers=_headers(csrf_a))
    assert res_a.status_code == 200
    assert len(res_a.json()) == 1

    # Maintainer B does not see Org A's rule
    res_b = client.get(f"{settings.api_v1_prefix}/monitoring/rules", headers=_headers(csrf_b))
    assert res_b.status_code == 200
    assert len(res_b.json()) == 0


def test_update_and_delete_rule(client: TestClient, db_session) -> None:
    """Maintainer can update rule threshold and soft/hard delete."""
    _, org_a, _, maintainer_a, _, _, _, _ = _setup_monitoring_context(db_session)
    _, _, csrf = _login(client, maintainer_a.email)

    res_create = client.post(
        f"{settings.api_v1_prefix}/monitoring/rules",
        json={
            "organization_id": str(org_a.id),
            "name": "Initial Bearing Rule",
            "measurement_type": "vibration",
            "operator": "gte",
            "threshold": 0.45,
            "unit": "simulated_index",
        },
        headers=_headers(csrf),
    )
    rule_id = res_create.json()["id"]

    # PATCH update
    res_patch = client.patch(
        f"{settings.api_v1_prefix}/monitoring/rules/{rule_id}",
        json={"threshold": 0.60, "name": "Updated Bearing Rule"},
        headers=_headers(csrf),
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["threshold"] == 0.60
    assert res_patch.json()["name"] == "Updated Bearing Rule"

    # DELETE
    res_del = client.delete(f"{settings.api_v1_prefix}/monitoring/rules/{rule_id}", headers=_headers(csrf))
    assert res_del.status_code == 204

    # Verify deleted
    res_verify = client.get(f"{settings.api_v1_prefix}/monitoring/rules/{rule_id}", headers=_headers(csrf))
    assert res_verify.status_code == 404


def test_rule_operator_validation(client: TestClient, db_session) -> None:
    """Unsupported operator is rejected with 422."""
    _, org_a, _, maintainer_a, _, _, _, _ = _setup_monitoring_context(db_session)
    _, _, csrf = _login(client, maintainer_a.email)

    res = client.post(
        f"{settings.api_v1_prefix}/monitoring/rules",
        json={
            "organization_id": str(org_a.id),
            "name": "Invalid Operator Rule",
            "measurement_type": "temperature",
            "operator": "arbitrary_eval",  # Invalid!
            "threshold": 100.0,
            "unit": "°C",
        },
        headers=_headers(csrf),
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Evaluation Engine & Alert Lifecycle Tests
# ---------------------------------------------------------------------------


def test_normal_readings_trigger_no_alerts(client: TestClient, db_session) -> None:
    """Readings within normal threshold boundaries generate zero alerts."""
    _, _, _, maintainer_a, _, motor_a, _, _ = _setup_monitoring_context(db_session)
    _, _, csrf = _login(client, maintainer_a.email)

    payload = _reading(str(motor_a.id), temp=52.0, vib=0.04)
    client.post(f"{settings.api_v1_prefix}/readings", json=payload, headers=_headers(csrf))

    res_alerts = client.get(
        f"{settings.api_v1_prefix}/alerts",
        params={"equipment_id": str(motor_a.id)},
        headers=_headers(csrf),
    )
    assert res_alerts.status_code == 200
    assert len(res_alerts.json()) == 0


def test_overheating_triggers_alert_with_structured_evidence(client: TestClient, db_session) -> None:
    """Violating reading generates an AnomalyEvent with evidence and an Open Alert."""
    _, org_a, _, maintainer_a, _, motor_a, _, motor_type = _setup_monitoring_context(db_session)
    _, _, csrf = _login(client, maintainer_a.email)

    # Configure rule: temperature > 75.0 °C
    client.post(
        f"{settings.api_v1_prefix}/monitoring/rules",
        json={
            "organization_id": str(org_a.id),
            "equipment_type_id": str(motor_type.id),
            "name": "Motor Overheating Protection",
            "measurement_type": "temperature",
            "operator": "gt",
            "threshold": 75.0,
            "unit": "°C",
            "severity": "critical",
        },
        headers=_headers(csrf),
    )

    # Ingest violating reading (88.5 °C)
    violating_reading = _reading(str(motor_a.id), temp=88.5, vib=0.05)
    ingest_res = client.post(
        f"{settings.api_v1_prefix}/readings",
        json=violating_reading,
        headers=_headers(csrf),
    )
    assert ingest_res.status_code == 201

    # Check alert was triggered
    alerts_res = client.get(
        f"{settings.api_v1_prefix}/alerts",
        params={"equipment_id": str(motor_a.id), "status": "open"},
        headers=_headers(csrf),
    )
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1

    alert = alerts[0]
    assert alert["status"] == "open"
    assert alert["severity"] == "critical"
    assert "Motor Overheating Protection" in alert["title"]

    # Verify detailed alert with linked AnomalyEvent and evidence
    detail_res = client.get(f"{settings.api_v1_prefix}/alerts/{alert['id']}", headers=_headers(csrf))
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["anomaly_event"] is not None
    ev = detail["anomaly_event"]
    assert ev["evidence_json"]["actual_value"] == 88.5
    assert ev["evidence_json"]["threshold"] == 75.0
    assert "Advisory alert" in ev["evidence_json"]["disclaimer"]


def test_duration_based_rule_evaluation(client: TestClient, db_session) -> None:
    """Rule with duration_seconds=10 requires sustained violation before alerting."""
    _, org_a, _, maintainer_a, _, motor_a, _, motor_type = _setup_monitoring_context(db_session)
    _, _, csrf = _login(client, maintainer_a.email)

    # Create duration rule: vibration > 0.40 for at least 10 seconds
    client.post(
        f"{settings.api_v1_prefix}/monitoring/rules",
        json={
            "organization_id": str(org_a.id),
            "equipment_type_id": str(motor_type.id),
            "name": "Sustained High Vibration",
            "measurement_type": "vibration",
            "operator": "gt",
            "threshold": 0.40,
            "unit": "simulated_index",
            "duration_seconds": 10,
            "severity": "high",
        },
        headers=_headers(csrf),
    )

    # 1. Single spike: only 1 reading -> duration window not yet met
    client.post(
        f"{settings.api_v1_prefix}/readings",
        json=_reading(str(motor_a.id), temp=50.0, vib=0.55, delta_s=0),
        headers=_headers(csrf),
    )
    alerts_1 = client.get(f"{settings.api_v1_prefix}/alerts", headers=_headers(csrf)).json()
    # No alert yet for "Sustained High Vibration"
    duration_alerts = [a for a in alerts_1 if "Sustained High Vibration" in a["title"]]
    assert len(duration_alerts) == 0

    # 2. Ingest readings spanning >= 10 seconds:
    now = datetime.now(UTC)
    batch_readings = []
    for i in range(5):
        r = _reading(str(motor_a.id), temp=50.0, vib=0.55)
        # 12 seconds ago, 9s ago, 6s ago, 3s ago, 0s ago
        r["timestamp"] = (now - timedelta(seconds=12 - (i * 3))).isoformat()
        r["source_event_id"] = f"sustained-{uuid.uuid4().hex[:8]}"
        batch_readings.append(r)

    client.post(
        f"{settings.api_v1_prefix}/readings/batch",
        json={"readings": batch_readings},
        headers=_headers(csrf),
    )

    alerts_2 = client.get(f"{settings.api_v1_prefix}/alerts", headers=_headers(csrf)).json()
    duration_alerts_2 = [a for a in alerts_2 if "Sustained High Vibration" in a["title"]]
    assert len(duration_alerts_2) == 1


def test_alert_lifecycle_acknowledge_and_resolve(client: TestClient, db_session) -> None:
    """Full lifecycle: open -> acknowledge -> resolve with resolution note."""
    _, org_a, _, maintainer_a, _, motor_a, _, _ = _setup_monitoring_context(db_session)
    _, _, csrf = _login(client, maintainer_a.email)

    # Ingest critical reading to trigger open alert
    client.post(
        f"{settings.api_v1_prefix}/readings",
        json=_reading(str(motor_a.id), temp=95.0, vib=0.85),
        headers=_headers(csrf),
    )

    alerts = client.get(f"{settings.api_v1_prefix}/alerts", headers=_headers(csrf)).json()
    assert len(alerts) >= 1
    alert_id = alerts[0]["id"]
    assert alerts[0]["status"] == "open"

    # 1. Acknowledge: POST /alerts/{id}/acknowledge
    ack_res = client.post(
        f"{settings.api_v1_prefix}/alerts/{alert_id}/acknowledge",
        json={"note": "Investigating cooling fan and lubrication"},
        headers=_headers(csrf),
    )
    assert ack_res.status_code == 200
    ack_alert = ack_res.json()
    assert ack_alert["status"] == "acknowledged"
    assert ack_alert["acknowledged_by"] == str(maintainer_a.id)
    assert ack_alert["acknowledged_at"] is not None

    # 2. Resolve: POST /alerts/{id}/resolve
    res_res = client.post(
        f"{settings.api_v1_prefix}/alerts/{alert_id}/resolve",
        json={"note": "Cleaned cooling fins and topped up bearing grease."},
        headers=_headers(csrf),
    )
    assert res_res.status_code == 200
    res_alert = res_res.json()
    assert res_alert["status"] == "resolved"
    assert res_alert["resolved_by"] == str(maintainer_a.id)
    assert res_alert["resolved_at"] is not None
    assert res_alert["resolution_note"] == "Cleaned cooling fins and topped up bearing grease."

    # 3. Cannot reopen resolved alert
    reopen_res = client.patch(
        f"{settings.api_v1_prefix}/alerts/{alert_id}/status",
        json={"status": "open"},
        headers=_headers(csrf),
    )
    assert reopen_res.status_code == 409


def test_alert_dismiss_lifecycle(client: TestClient, db_session) -> None:
    """Maintainer can dismiss an alert deemed transient/false positive."""
    _, org_a, _, maintainer_a, _, motor_a, _, _ = _setup_monitoring_context(db_session)
    _, _, csrf = _login(client, maintainer_a.email)

    client.post(
        f"{settings.api_v1_prefix}/readings",
        json=_reading(str(motor_a.id), temp=92.0, vib=0.05),
        headers=_headers(csrf),
    )
    alerts = client.get(f"{settings.api_v1_prefix}/alerts", headers=_headers(csrf)).json()
    alert_id = alerts[0]["id"]

    res = client.post(
        f"{settings.api_v1_prefix}/alerts/{alert_id}/dismiss",
        json={"note": "Known thermal load test; dismissing alert."},
        headers=_headers(csrf),
    )
    assert res.status_code == 200
    dismissed = res.json()
    assert dismissed["status"] == "dismissed"
    assert dismissed["resolution_note"] == "Known thermal load test; dismissing alert."


def test_cross_tenant_alert_isolation(client: TestClient, db_session) -> None:
    """Maintainer B cannot view or acknowledge Org A's alerts."""
    _, org_a, org_b, maintainer_a, maintainer_b, motor_a, _, _ = _setup_monitoring_context(db_session)
    _, _, csrf_a = _login(client, maintainer_a.email)
    _, _, csrf_b = _login(client, maintainer_b.email)

    # Org A generates alert
    client.post(
        f"{settings.api_v1_prefix}/readings",
        json=_reading(str(motor_a.id), temp=93.0, vib=0.8),
        headers=_headers(csrf_a),
    )
    alert_a = client.get(f"{settings.api_v1_prefix}/alerts", headers=_headers(csrf_a)).json()[0]

    # Maintainer B queries alerts -> does not see Org A's alert
    alerts_b = client.get(f"{settings.api_v1_prefix}/alerts", headers=_headers(csrf_b)).json()
    assert all(a["id"] != alert_a["id"] for a in alerts_b)

    # Maintainer B tries to acknowledge Org A's alert -> 403 Forbidden
    ack_res = client.post(
        f"{settings.api_v1_prefix}/alerts/{alert_a['id']}/acknowledge",
        headers=_headers(csrf_b),
    )
    assert ack_res.status_code == 403


def test_equipment_status_and_overview(client: TestClient, db_session) -> None:
    """Equipment status reports latest reading, staleness, and open alert counts."""
    _, org_a, _, maintainer_a, _, motor_a, _, _ = _setup_monitoring_context(db_session)
    _, _, csrf = _login(client, maintainer_a.email)

    # Ingest a reading
    client.post(
        f"{settings.api_v1_prefix}/readings",
        json=_reading(str(motor_a.id), temp=60.0, vib=0.06),
        headers=_headers(csrf),
    )

    # GET /equipment/{id}/status
    res_status = client.get(
        f"{settings.api_v1_prefix}/equipment/{motor_a.id}/status",
        headers=_headers(csrf),
    )
    assert res_status.status_code == 200
    st = res_status.json()
    assert st["equipment_id"] == str(motor_a.id)
    assert st["name"] == motor_a.name
    assert st["latest_reading"] is not None
    assert st["latest_reading"]["temperature_c"] == 60.0
    assert st["is_stale"] is False

    # GET /monitoring/overview
    res_overview = client.get(f"{settings.api_v1_prefix}/monitoring/overview", headers=_headers(csrf))
    assert res_overview.status_code == 200
    overview = res_overview.json()
    assert len(overview) >= 1
    assert any(item["equipment_id"] == str(motor_a.id) for item in overview)


def test_simulator_overheating_scenario_triggers_reproducible_alert(
    client: TestClient,
    db_session,
) -> None:
    """Exit criterion for Phase 4: A known simulated fault scenario triggers reproducible alert with evidence."""
    _, org_a, _, maintainer_a, _, motor_a, _, motor_type = _setup_monitoring_context(db_session)
    _, _, csrf = _login(client, maintainer_a.email)

    # 1. Configure alert rule on motor equipment
    client.post(
        f"{settings.api_v1_prefix}/monitoring/rules",
        json={
            "organization_id": str(org_a.id),
            "equipment_type_id": str(motor_type.id),
            "name": "Overheating Threshold",
            "measurement_type": "temperature",
            "operator": "gt",
            "threshold": 70.0,
            "unit": "°C",
            "severity": "critical",
        },
        headers=_headers(csrf),
    )

    # 2. Run deterministic simulator with 'overheating' scenario
    generator = ReadingGenerator(
        equipment_id=str(motor_a.id),
        scenario_id="overheating",
        scenario_label="overheating",
        seed=12345,  # Fixed seed for reproducibility
        interval_seconds=1.0,
    )

    # Generate 60 steps of the overheating scenario
    steps = list(generator.stream(perturbation_fn=overheating_perturbation, max_steps=60))
    # Batch ingest into API
    ingest_res = client.post(
        f"{settings.api_v1_prefix}/readings/batch",
        json={"readings": steps},
        headers=_headers(csrf),
    )
    assert ingest_res.status_code == 201

    # 3. Verify alert was triggered
    alerts_res = client.get(
        f"{settings.api_v1_prefix}/alerts",
        params={"equipment_id": str(motor_a.id)},
        headers=_headers(csrf),
    )
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1

    overheat_alert = next((a for a in alerts if "Overheating Threshold" in a["title"]), None)
    assert overheat_alert is not None, "Overheating scenario must trigger the configured rule alert"
    assert overheat_alert["severity"] == "critical"

    # 4. Verify evidence
    detail_res = client.get(f"{settings.api_v1_prefix}/alerts/{overheat_alert['id']}", headers=_headers(csrf))
    detail = detail_res.json()
    assert detail["anomaly_event"] is not None
    evidence = detail["anomaly_event"]["evidence_json"]
    assert evidence["actual_value"] > 70.0
    assert evidence["operator"] == "gt"
    assert evidence["threshold"] == 70.0
    assert "disclaimer" in evidence

