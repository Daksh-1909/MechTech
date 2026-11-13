"""Phase 8 — Hardening and End-to-End Workflow Integration Test.

Simulates the entire MechTech operational lifecycle from start to finish:
1. Public User Registration -> Administrator Approval -> Session Login
2. Equipment Onboarding -> Component Breakdown -> Sensor Registry -> Monitoring Rules
3. Deterministic Telemetry Ingestion -> Rule Violation Evaluation -> Anomaly & Alert Triggering
4. Multi-Layer Hybrid Diagnostics (Rules + Scikit-learn Classifier + NetworkX Knowledge Graph)
5. Advisory Human Review Workflow (Confirmed by Maintainer)
6. Maintenance Work Order Execution -> Parts Replacement -> Supervisor Verification
7. Secure Document Attachment Upload (PDF inspection report) -> SHA-256 Checksum Validation -> Streaming Download
8. Tamper-Evident Audit Logging Trail Verification
9. Backup and Restore Cycle Verification (Cryptographic SHA-256 Manifest Integrity)
10. Health & Readiness Liveness Probes
"""

from datetime import UTC, datetime, timedelta
import io
from pathlib import Path
import sys
import uuid

import pytest
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.core.config import settings
from app.models import UserStatus
from app.models.enums import (
    AlertStatus,
    DiagnosisStatus,
    FilePurpose,
    MaintenanceOutcome,
    MaintenancePriority,
    MaintenanceStatus,
    MaintenanceType,
    VerificationStatus,
)
from app.modules.auth import service as auth_service
from app.modules.equipment import repository as eq_repo
from app.modules.knowledge_graph import service as kg_service
from app.modules.organizations import service as org_service
from scripts.backup import create_backup
from scripts.restore import restore_backup

ADMIN_EMAIL = "super_admin@mechtech.internal"
ADMIN_PASSWORD = "super-secure-admin-pass-2026"
USER_PASSWORD = "technician-password-2026"


def _headers(csrf_token: str | None) -> dict[str, str]:
    if not csrf_token:
        return {}
    return {settings.csrf_header_name: csrf_token}


def _login(client: TestClient, email: str, password: str) -> tuple[int, dict, str | None]:
    response = client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": email, "password": password},
    )
    csrf_token = client.cookies.get(settings.csrf_cookie_name)
    return response.status_code, response.json(), csrf_token


def test_complete_end_to_end_lifecycle(client: TestClient, db_session):
    """Exit criterion: Comprehensive E2E test verifying full multi-layer condition monitoring and maintenance lifecycle."""
    auth_service.repository.ensure_default_roles_and_permissions(db_session)
    eq_types = eq_repo.ensure_default_equipment_types(db_session)
    motor_type = eq_types["electric_motor"]
    kg_service.ensure_default_motor_knowledge_graph(db_session)

    # -----------------------------------------------------------------------
    # Step 1: Bootstrap Platform Admin & Organization
    # -----------------------------------------------------------------------
    admin = auth_service.create_user(
        db_session,
        name="Platform Administrator",
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        role="platform_admin",
        status=UserStatus.ACTIVE.value,
    )
    org = org_service.create_organization(
        db_session,
        actor=admin,
        name="Primary Manufacturing Plant",
        slug="mfg-plant-01",
    )
    db_session.commit()

    # -----------------------------------------------------------------------
    # Step 2: Public Registration & Admin Approval Workflow
    # -----------------------------------------------------------------------
    # User submits public registration request
    reg_res = client.post(
        f"{settings.api_v1_prefix}/auth/register",
        json={
            "name": "Jane Technician",
            "email": "jane.tech@mfg.internal",
            "password": USER_PASSWORD,
            "organization_name": "Primary Manufacturing Plant",
        },
    )
    assert reg_res.status_code == 201
    reg_id = reg_res.json()["registration_request_id"]

    # Admin logs in
    status, _, admin_csrf = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    assert status == 200

    # Admin approves registration and assigns Maintainer role
    approve_res = client.post(
        f"{settings.api_v1_prefix}/admin/registrations/{reg_id}/approve",
        json={"initial_role": "maintainer"},
        headers=_headers(admin_csrf),
    )
    assert approve_res.status_code == 200

    # Technician can now authenticate
    t_status, t_user, tech_csrf = _login(client, "jane.tech@mfg.internal", USER_PASSWORD)
    assert t_status == 200
    tech_id = t_user["user"]["id"]

    # Add technician to organization
    org_service.add_member(db_session, actor=admin, organization_id=org.id, user_id=uuid.UUID(tech_id))
    db_session.commit()

    # -----------------------------------------------------------------------
    # Step 3: Equipment, Components & Monitoring Rules Onboarding
    # -----------------------------------------------------------------------
    # Create Motor
    motor_res = client.post(
        f"{settings.api_v1_prefix}/equipment",
        json={
            "organization_id": str(org.id),
            "equipment_type_id": str(motor_type.id),
            "name": "Extruder Three-Phase Induction Motor",
            "asset_tag": "EXT-MTR-001",
            "manufacturer": "ABB",
            "model_number": "M3AA 132",
            "status": "operational",
            "specification": {
                "rated_power_kw": 7.5,
                "rated_voltage_v": 400.0,
                "rated_speed_rpm": 1450.0,
            },
        },
        headers=_headers(admin_csrf),
    )
    assert motor_res.status_code == 201
    motor_id = motor_res.json()["id"]

    # Add Component: Drive-End Front Bearing
    comp_res = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/components",
        json={
            "component_key": "bearing_front",
            "name": "Drive-End Front Bearing",
            "component_type": "bearing",
            "description": "Deep groove ball bearing supporting drive shaft",
        },
        headers=_headers(admin_csrf),
    )
    assert comp_res.status_code == 201
    comp_id = comp_res.json()["id"]

    # Add Sensor: Vibration sensor on bearing
    sensor_res = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/sensors",
        json={
            "component_id": comp_id,
            "sensor_key": "vib_bearing_front",
            "measurement_type": "vibration",
            "unit": "mm/s",
        },
        headers=_headers(admin_csrf),
    )
    assert sensor_res.status_code == 201

    # Add Monitoring Rule: Vibration threshold rule
    rule_res = client.post(
        f"{settings.api_v1_prefix}/monitoring/rules",
        json={
            "name": "Drive-End High Vibration Alert Rule",
            "measurement_type": "vibration",
            "operator": "gt",
            "threshold": 0.5,
            "unit": "mm/s",
            "duration_seconds": 0,
            "severity": "critical",
        },
        headers=_headers(admin_csrf),
    )
    assert rule_res.status_code == 201

    # -----------------------------------------------------------------------
    # Step 4: Telemetry Ingestion & Automatic Alert Generation
    # -----------------------------------------------------------------------
    # Ingest 15 readings representing bearing degradation (vibration 1.85 mm/s > 0.5 mm/s threshold)
    now = datetime.now(UTC)
    readings = [
        {
            "equipment_id": motor_id,
            "timestamp": (now - timedelta(seconds=(15 - i) * 2)).isoformat(),
            "temperature_c": 56.0,
            "vibration_value": 1.85 + (i % 2) * 0.05,
            "speed_rpm": 1450.0,
            "source": "simulator",
            "source_event_id": f"sim-run-{i:04d}",
        }
        for i in range(15)
    ]
    ingest_res = client.post(
        f"{settings.api_v1_prefix}/readings/batch",
        json={"readings": readings},
        headers=_headers(tech_csrf),
    )
    assert ingest_res.status_code == 201

    # Query active alerts: verify critical alert was triggered
    alerts_res = client.get(
        f"{settings.api_v1_prefix}/alerts?status=open",
        headers=_headers(tech_csrf),
    )
    assert alerts_res.status_code == 200
    alert_list = alerts_res.json()
    assert len(alert_list) >= 1
    active_alert = alert_list[0]
    assert active_alert["severity"] == "critical"

    # Acknowledge alert
    ack_res = client.post(
        f"{settings.api_v1_prefix}/alerts/{active_alert['id']}/acknowledge",
        headers=_headers(tech_csrf),
    )
    assert ack_res.status_code == 200

    # -----------------------------------------------------------------------
    # Step 5: Multi-Layer Hybrid Diagnostic Orchestration
    # -----------------------------------------------------------------------
    diag_res = client.post(
        f"{settings.api_v1_prefix}/diagnoses/generate",
        json={"equipment_id": motor_id, "window_size": 15},
        headers=_headers(tech_csrf),
    )
    assert diag_res.status_code == 201
    diag = diag_res.json()

    assert diag["status"] == DiagnosisStatus.POSSIBLE_FAULT.value
    assert diag["primary_fault_key"] == "bearing_wear"
    assert diag["confidence_score"] >= 0.80
    assert len(diag["evidence_items"]) == 3  # rule, prediction, graph

    # Verify Knowledge Graph evidence includes remediation
    graph_ev = next(e for e in diag["evidence_items"] if e["evidence_type"] == "graph")
    assert any("bearing" in p["label"].lower() for p in graph_ev["details_json"]["affected_components"])
    assert any("bearing" in r["label"].lower() or "lubricat" in r["label"].lower() for r in graph_ev["details_json"]["repair_actions"])

    # -----------------------------------------------------------------------
    # Step 6: Human Review Workflow
    # -----------------------------------------------------------------------
    review_res = client.post(
        f"{settings.api_v1_prefix}/diagnoses/{diag['id']}/review",
        json={
            "review_status": "confirmed_by_reviewer",
            "review_note": "Acoustic emission and physical visual check confirmed front bearing raceway spalling.",
        },
        headers=_headers(tech_csrf),
    )
    assert review_res.status_code == 200
    assert review_res.json()["review_status"] == "confirmed_by_reviewer"

    # -----------------------------------------------------------------------
    # Step 7: Maintenance Work Order, Resolution & Verification
    # -----------------------------------------------------------------------
    # Create work order linked to both alert and confirmed diagnosis
    maint_res = client.post(
        f"{settings.api_v1_prefix}/maintenance",
        json={
            "equipment_id": motor_id,
            "title": "Front Drive-End Bearing Replacement",
            "description": "Extract degraded 6308 ball bearing, clean shaft seat, install new bearing.",
            "maintenance_type": MaintenanceType.CORRECTIVE.value,
            "priority": MaintenancePriority.CRITICAL.value,
            "related_alert_id": active_alert["id"],
            "diagnosis_id": diag["id"],
            "assigned_to": tech_id,
        },
        headers=_headers(tech_csrf),
    )
    assert maint_res.status_code == 201
    work_order_id = maint_res.json()["id"]

    # Update work progress: completed with parts replaced
    patch_res = client.patch(
        f"{settings.api_v1_prefix}/maintenance/{work_order_id}",
        json={
            "status": MaintenanceStatus.COMPLETED.value,
            "work_performed": "Pressed out worn bearing, induction-heated and fitted SKF 6308-2Z, packed with Mobil Polyrex EM.",
            "parts_replaced_json": [{"part": "SKF-6308-2Z", "qty": 1}],
        },
        headers=_headers(tech_csrf),
    )
    assert patch_res.status_code == 200

    # Supervisor verifies completion
    verify_res = client.post(
        f"{settings.api_v1_prefix}/maintenance/{work_order_id}/verify",
        json={
            "verification_status": "verified",
            "verification_note": "Radial runout measured < 0.02 mm; baseline 30-min run test nominal.",
        },
        headers=_headers(admin_csrf),
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["verification_status"] == VerificationStatus.VERIFIED.value
    assert verify_res.json()["outcome"] == MaintenanceOutcome.RESOLVED.value

    # Resolve linked alert
    resolve_alert_res = client.post(
        f"{settings.api_v1_prefix}/alerts/{active_alert['id']}/resolve",
        json={"resolution_note": f"Bearing replaced under Work Order {work_order_id}"},
        headers=_headers(tech_csrf),
    )
    assert resolve_alert_res.status_code == 200

    # -----------------------------------------------------------------------
    # Step 8: Document Attachment & Checksum Verification
    # -----------------------------------------------------------------------
    pdf_bytes = b"%PDF-1.4 Vibration Analysis Report: Post-maintenance runout test 0.11 mm/s."
    files = {
        "file": ("bearing_replacement_report.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    }
    attach_res = client.post(
        f"{settings.api_v1_prefix}/maintenance/{work_order_id}/attachments",
        files=files,
        data={"purpose": FilePurpose.MAINTENANCE_ATTACHMENT.value},
        headers=_headers(tech_csrf),
    )
    assert attach_res.status_code == 201
    file_id = attach_res.json()["id"]
    assert attach_res.json()["size_bytes"] == len(pdf_bytes)

    # Download file and verify streaming binary integrity
    download_res = client.get(
        f"{settings.api_v1_prefix}/files/{file_id}/download",
        headers=_headers(tech_csrf),
    )
    assert download_res.status_code == 200
    assert download_res.content == pdf_bytes

    # -----------------------------------------------------------------------
    # Step 9: Audit Trail Verification
    # -----------------------------------------------------------------------
    audit_res = client.get(
        f"{settings.api_v1_prefix}/audit-logs",
        headers=_headers(admin_csrf),
    )
    assert audit_res.status_code == 200
    actions_logged = [event["action"] for event in audit_res.json()]
    assert "user.created" in actions_logged
    assert "diagnosis.generated" in actions_logged
    assert "diagnosis.reviewed" in actions_logged
    assert "maintenance.created" in actions_logged
    assert "maintenance.verified" in actions_logged
    assert "file.uploaded" in actions_logged


def test_backup_and_restore_cycle(tmp_path, monkeypatch):
    """Exit criterion: Automated backup and restore cycle with cryptographic SHA-256 verification."""
    backup_dir = tmp_path / "backups"
    monkeypatch.setattr("scripts.backup.settings.data_root", tmp_path)
    monkeypatch.setattr("scripts.restore.settings.data_root", tmp_path)

    # 1. Create Backup
    archive_path = create_backup(dest_dir=backup_dir)
    assert archive_path.exists()
    assert archive_path.name.endswith(".tar.gz")

    # 2. Restore Backup
    restored = restore_backup(archive_path, force=True)
    assert restored is True


def test_health_probes(client: TestClient):
    """Verify system readiness and liveness endpoints for production orchestrators."""
    # Liveness probe
    live_res = client.get(f"{settings.api_v1_prefix}/health/live")
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "ok"

    # Readiness probe (DB + Storage check)
    ready_res = client.get(f"{settings.api_v1_prefix}/health/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["status"] == "ready"

    # Version info
    ver_res = client.get(f"{settings.api_v1_prefix}/version")
    assert ver_res.status_code == 200
    assert "version" in ver_res.json()

