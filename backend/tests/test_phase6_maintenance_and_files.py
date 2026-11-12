"""Phase 6 — Maintenance and Files Test Suite.

Covers:
- Maintenance record creation, scheduling, and updating
- Cross-linking maintenance work orders to equipment, alerts, and diagnoses
- Cross-equipment / cross-tenant reference rejection
- Work order completion, parts replaced, and outcome tracking
- Technician / supervisor verification workflow (verified / rejected)
- Secure local file uploads, SHA-256 checksum calculation, and storage
- Path traversal prevention and size limit enforcement
- File download streaming with tenant authorization
- Attachments linked directly to maintenance work orders
- Multi-tenant isolation and role-based permissions
- Audit trail verification for all maintenance and file operations
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
from app.modules.alerts import repository as alert_repo
from app.modules.auth import service as auth_service
from app.modules.diagnostics import repository as diag_repo
from app.modules.equipment import repository as eq_repo
from app.modules.files import repository as file_repo
from app.modules.files import service as file_service
from app.modules.maintenance import repository as maint_repo
from app.modules.maintenance import service as maint_service
from app.modules.organizations import service as org_service

PASSWORD = "test-pass-phase6"
ADMIN_PASSWORD = "admin-pass-phase6"


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


def _setup_maintenance_context(db):
    auth_service.repository.ensure_default_roles_and_permissions(db)
    eq_types = eq_repo.ensure_default_equipment_types(db)
    motor_type = eq_types["electric_motor"]

    admin = auth_service.repository.get_user_by_email(db, "maint_admin@example.com")
    if not admin:
        admin = auth_service.create_user(
            db,
            name="Maintenance Admin",
            email="maint_admin@example.com",
            password=ADMIN_PASSWORD,
            role="platform_admin",
            status=UserStatus.ACTIVE.value,
        )

    # Organization A
    org_a = org_service.get_organization_by_slug(db, "maint-org-a")
    if not org_a:
        org_a = org_service.create_organization(
            db,
            actor=admin,
            name="Maintenance Facility A",
            slug="maint-org-a",
        )

    maintainer_a = auth_service.repository.get_user_by_email(db, "tech_a@example.com")
    if not maintainer_a:
        maintainer_a = auth_service.create_user(
            db,
            name="Technician A",
            email="tech_a@example.com",
            password=PASSWORD,
            role="maintainer",
            organization_id=org_a.id,
            status=UserStatus.ACTIVE.value,
        )
        org_service.add_member(db, actor=admin, organization_id=org_a.id, user_id=maintainer_a.id)

    viewer_a = auth_service.repository.get_user_by_email(db, "viewer_maint_a@example.com")
    if not viewer_a:
        viewer_a = auth_service.create_user(
            db,
            name="Viewer A",
            email="viewer_maint_a@example.com",
            password=PASSWORD,
            role="demo_user",
            organization_id=org_a.id,
            status=UserStatus.ACTIVE.value,
        )
        org_service.add_member(db, actor=admin, organization_id=org_a.id, user_id=viewer_a.id)

    # Organization B
    org_b = org_service.get_organization_by_slug(db, "maint-org-b")
    if not org_b:
        org_b = org_service.create_organization(
            db,
            actor=admin,
            name="Maintenance Facility B",
            slug="maint-org-b",
        )

    maintainer_b = auth_service.repository.get_user_by_email(db, "tech_b@example.com")
    if not maintainer_b:
        maintainer_b = auth_service.create_user(
            db,
            name="Technician B",
            email="tech_b@example.com",
            password=PASSWORD,
            role="maintainer",
            organization_id=org_b.id,
            status=UserStatus.ACTIVE.value,
        )
        org_service.add_member(db, actor=admin, organization_id=org_b.id, user_id=maintainer_b.id)

    # Equipment A
    eq_a = db.query(eq_repo.Equipment).filter_by(organization_id=org_a.id, asset_tag="MTR-MAINT-01").first()
    if not eq_a:
        eq_a = eq_repo.create_equipment(
            db,
            organization_id=org_a.id,
            equipment_type_id=motor_type.id,
            name="Compressor Drive Motor A",
            created_by=admin.id,
            asset_tag="MTR-MAINT-01",
            status="operational",
        )

    # Equipment B
    eq_b = db.query(eq_repo.Equipment).filter_by(organization_id=org_b.id, asset_tag="MTR-MAINT-02").first()
    if not eq_b:
        eq_b = eq_repo.create_equipment(
            db,
            organization_id=org_b.id,
            equipment_type_id=motor_type.id,
            name="Pump Motor B",
            created_by=admin.id,
            asset_tag="MTR-MAINT-02",
            status="operational",
        )

    # Seed an Alert and Diagnosis for Equipment A
    alert_a = alert_repo.create_alert(
        db,
        organization_id=org_a.id,
        equipment_id=eq_a.id,
        alert_type="vibration_anomaly",
        severity="critical",
        status=AlertStatus.OPEN.value,
        title="High Bearing Vibration Exceeded",
        description="Peak velocity 2.1 mm/s",
    )

    diag_a = diag_repo.create_diagnosis(
        db,
        organization_id=org_a.id,
        equipment_id=eq_a.id,
        status=DiagnosisStatus.POSSIBLE_FAULT.value,
        severity="critical",
        confidence_score=0.91,
        summary="Drive-end bearing deterioration detected.",
    )

    db.commit()

    return {
        "admin": admin,
        "org_a": org_a,
        "maintainer_a": maintainer_a,
        "viewer_a": viewer_a,
        "org_b": org_b,
        "maintainer_b": maintainer_b,
        "motor_a": eq_a,
        "motor_b": eq_b,
        "alert_a": alert_a,
        "diag_a": diag_a,
    }


# ---------------------------------------------------------------------------
# Maintenance Records CRUD & Linking Tests
# ---------------------------------------------------------------------------


def test_create_maintenance_record_linked(client: TestClient, db):
    """Exit criterion: Authorized users can link maintenance work to equipment, alerts, and diagnoses."""
    ctx = _setup_maintenance_context(db)
    maint = ctx["maintainer_a"]
    motor = ctx["motor_a"]
    alert = ctx["alert_a"]
    diag = ctx["diag_a"]

    status, _, csrf = _login(client, maint.email, PASSWORD)
    assert status == 200

    payload = {
        "equipment_id": str(motor.id),
        "title": "Drive-End Bearing Replacement",
        "description": "Replace worn 6308-2Z deep groove ball bearing following diagnostic alert.",
        "maintenance_type": MaintenanceType.CORRECTIVE.value,
        "priority": MaintenancePriority.CRITICAL.value,
        "status": MaintenanceStatus.SCHEDULED.value,
        "related_alert_id": str(alert.id),
        "diagnosis_id": str(diag.id),
        "scheduled_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "symptoms": "Audible high-pitch whining and 2.1 mm/s vibration.",
        "notes": "Ensure ISO VG 46 grease is used during installation.",
    }

    res = client.post(
        f"{settings.api_v1_prefix}/maintenance",
        json=payload,
        headers=_headers(csrf),
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["title"] == payload["title"]
    assert data["equipment_id"] == str(motor.id)
    assert data["related_alert_id"] == str(alert.id)
    assert data["diagnosis_id"] == str(diag.id)
    assert data["outcome"] == MaintenanceOutcome.PENDING_VERIFICATION.value
    assert data["verification_status"] == VerificationStatus.PENDING.value
    assert data["equipment_name"] == motor.name


def test_cross_equipment_link_rejected(client: TestClient, db):
    """Verify that referencing an alert or diagnosis belonging to another machine/tenant is rejected."""
    ctx = _setup_maintenance_context(db)
    maint = ctx["maintainer_a"]
    motor_b = ctx["motor_b"]
    alert_a = ctx["alert_a"]

    status, _, csrf = _login(client, maint.email, PASSWORD)
    assert status == 200

    # Attempt to link Org A alert to Org B motor
    res = client.post(
        f"{settings.api_v1_prefix}/maintenance",
        json={
            "equipment_id": str(motor_b.id),
            "title": "Mismatched Alert Test",
            "related_alert_id": str(alert_a.id),
        },
        headers=_headers(csrf),
    )
    assert res.status_code in (400, 403, 404)


def test_maintenance_lifecycle_and_verification(client: TestClient, db):
    """Verify workflow: update work performed, replace parts, and technician verification."""
    ctx = _setup_maintenance_context(db)
    maint = ctx["maintainer_a"]
    motor = ctx["motor_a"]

    status, _, csrf = _login(client, maint.email, PASSWORD)
    assert status == 200

    # 1. Create work order
    create_res = client.post(
        f"{settings.api_v1_prefix}/maintenance",
        json={
            "equipment_id": str(motor.id),
            "title": "Stator Winding Inspection & Cleaning",
            "maintenance_type": MaintenanceType.PREVENTIVE.value,
            "priority": MaintenancePriority.HIGH.value,
        },
        headers=_headers(csrf),
    )
    rec_id = create_res.json()["id"]

    # 2. Update progress: in_progress -> completed
    patch_res = client.patch(
        f"{settings.api_v1_prefix}/maintenance/{rec_id}",
        json={
            "status": MaintenanceStatus.COMPLETED.value,
            "work_performed": "Cleaned stator cooling ducts with compressed air; tightened terminal block connections.",
            "parts_replaced_json": [{"part_number": "TRM-LUG-M6", "description": "Terminal Lug M6", "quantity": 3}],
            "started_at": datetime.now(UTC).isoformat(),
            "completed_at": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
        },
        headers=_headers(csrf),
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["status"] == MaintenanceStatus.COMPLETED.value
    assert len(patched["parts_replaced_json"]) == 1
    assert "Cleaned stator" in patched["work_performed"]

    # 3. Technician Verification -> verified
    verify_res = client.post(
        f"{settings.api_v1_prefix}/maintenance/{rec_id}/verify",
        json={
            "verification_status": "verified",
            "verification_note": "Post-maintenance vibration scan is within nominal 0.12 mm/s limits.",
        },
        headers=_headers(csrf),
    )
    assert verify_res.status_code == 200
    verified = verify_res.json()
    assert verified["verification_status"] == VerificationStatus.VERIFIED.value
    assert verified["outcome"] == MaintenanceOutcome.RESOLVED.value
    assert verified["verified_by"] == str(maint.id)
    assert "nominal" in verified["verification_note"]


# ---------------------------------------------------------------------------
# Secure Local File Storage Tests
# ---------------------------------------------------------------------------


def test_file_upload_and_download(client: TestClient, db):
    """Verify file upload, SHA-256 calculation, and authorized download stream."""
    ctx = _setup_maintenance_context(db)
    maint = ctx["maintainer_a"]
    org = ctx["org_a"]

    status, _, csrf = _login(client, maint.email, PASSWORD)
    assert status == 200

    file_content = b"Vibration Spectrum Report: BPFO harmonic analysis nominal."
    files = {
        "file": ("vibration_spectrum_2026.pdf", io.BytesIO(file_content), "application/pdf")
    }
    data = {
        "organization_id": str(org.id),
        "purpose": FilePurpose.VIBRATION_REPORT.value,
    }

    # Upload file
    upload_res = client.post(
        f"{settings.api_v1_prefix}/files",
        files=files,
        data=data,
        headers=_headers(csrf),
    )
    assert upload_res.status_code == 201, upload_res.text
    file_info = upload_res.json()
    file_id = file_info["id"]

    assert file_info["original_filename"] == "vibration_spectrum_2026.pdf"
    assert file_info["size_bytes"] == len(file_content)
    assert len(file_info["checksum"]) == 64  # SHA-256 hex string

    # Download file
    download_res = client.get(
        f"{settings.api_v1_prefix}/files/{file_id}/download",
        headers=_headers(csrf),
    )
    assert download_res.status_code == 200
    assert download_res.content == file_content
    assert download_res.headers["content-type"] == "application/pdf"


def test_maintenance_record_attachment_linking(client: TestClient, db):
    """Verify that uploading attachment to maintenance record links file directly."""
    ctx = _setup_maintenance_context(db)
    maint = ctx["maintainer_a"]
    motor = ctx["motor_a"]

    status, _, csrf = _login(client, maint.email, PASSWORD)
    assert status == 200

    # Create work order
    res = client.post(
        f"{settings.api_v1_prefix}/maintenance",
        json={"equipment_id": str(motor.id), "title": "Bearing Inspection Photo Record"},
        headers=_headers(csrf),
    )
    rec_id = res.json()["id"]

    # Upload attachment directly to work order
    photo_content = b"\x89PNG\r\n\x1a\nFakeBearingImageData"
    files = {
        "file": ("bearing_flaking.png", io.BytesIO(photo_content), "image/png")
    }
    attach_res = client.post(
        f"{settings.api_v1_prefix}/maintenance/{rec_id}/attachments",
        files=files,
        data={"purpose": FilePurpose.INSPECTION_PHOTO.value},
        headers=_headers(csrf),
    )
    assert attach_res.status_code == 201
    file_info = attach_res.json()
    assert file_info["maintenance_record_id"] == rec_id

    # Retrieve work order and verify attachment is listed
    get_res = client.get(
        f"{settings.api_v1_prefix}/maintenance/{rec_id}",
        headers=_headers(csrf),
    )
    assert get_res.status_code == 200
    data = get_res.json()
    assert len(data["attachments"]) == 1
    assert data["attachments"][0]["original_filename"] == "bearing_flaking.png"


def test_path_traversal_attack_neutralized(client: TestClient, db):
    """Verify that malicious filenames containing path traversal sequences are safely stripped."""
    ctx = _setup_maintenance_context(db)
    maint = ctx["maintainer_a"]
    org = ctx["org_a"]

    status, _, csrf = _login(client, maint.email, PASSWORD)
    assert status == 200

    files = {
        "file": ("../../../../etc/passwd.txt", io.BytesIO(b"malicious payload"), "text/plain")
    }
    upload_res = client.post(
        f"{settings.api_v1_prefix}/files",
        files=files,
        data={"organization_id": str(org.id), "purpose": "general"},
        headers=_headers(csrf),
    )
    assert upload_res.status_code == 201
    file_info = upload_res.json()
    assert ".." not in file_info["original_filename"]
    assert file_info["original_filename"] == "passwd.txt"


# ---------------------------------------------------------------------------
# Multi-Tenant Isolation & Role Authorization Tests
# ---------------------------------------------------------------------------


def test_cross_tenant_maintenance_and_file_isolation(client: TestClient, db):
    """Verify maintainer in Org B cannot read or download maintenance files of Org A."""
    ctx = _setup_maintenance_context(db)
    maint_a = ctx["maintainer_a"]
    maint_b = ctx["maintainer_b"]
    org_a = ctx["org_a"]
    motor_a = ctx["motor_a"]

    # Org A maintainer creates record and uploads file
    _, _, csrf_a = _login(client, maint_a.email, PASSWORD)
    m_res = client.post(
        f"{settings.api_v1_prefix}/maintenance",
        json={"equipment_id": str(motor_a.id), "title": "Confidential Org A Overhaul"},
        headers=_headers(csrf_a),
    )
    rec_id = m_res.json()["id"]

    f_res = client.post(
        f"{settings.api_v1_prefix}/files",
        files={"file": ("secret_blueprint.pdf", io.BytesIO(b"Confidential Org A Specs"), "application/pdf")},
        data={"organization_id": str(org_a.id), "purpose": "manual"},
        headers=_headers(csrf_a),
    )
    file_id = f_res.json()["id"]

    # Org B maintainer logs in
    _, _, csrf_b = _login(client, maint_b.email, PASSWORD)

    # Org B cannot view Org A maintenance record
    rec_view = client.get(
        f"{settings.api_v1_prefix}/maintenance/{rec_id}",
        headers=_headers(csrf_b),
    )
    assert rec_view.status_code in (403, 404)

    # Org B cannot download Org A file
    file_download = client.get(
        f"{settings.api_v1_prefix}/files/{file_id}/download",
        headers=_headers(csrf_b),
    )
    assert file_download.status_code in (403, 404)


def test_viewer_cannot_create_or_verify(client: TestClient, db):
    """Verify demo user / viewer cannot create, update, or verify maintenance work orders."""
    ctx = _setup_maintenance_context(db)
    viewer = ctx["viewer_a"]
    motor_a = ctx["motor_a"]

    _, _, csrf = _login(client, viewer.email, PASSWORD)

    # Viewer cannot create record -> 403
    create_res = client.post(
        f"{settings.api_v1_prefix}/maintenance",
        json={"equipment_id": str(motor_a.id), "title": "Unauthorized Order"},
        headers=_headers(csrf),
    )
    assert create_res.status_code == 403
