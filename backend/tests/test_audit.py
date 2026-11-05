import json

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.models import AuditLog, User, UserRole
from app.modules.audit.actions import AuditAction
from app.modules.audit.service import sanitize_metadata
from app.modules.auth import service

PASSWORD = "correct-horse-battery"
NEW_PASSWORD = "battery-staple-horse"


def _create_user(db, *, email: str, role: UserRole) -> User:
    return service.create_user(
        db,
        name=f"{role.value.title()} User",
        email=email,
        password=PASSWORD,
        role=role,
    )


def _login(client: TestClient, email: str, password: str = PASSWORD) -> dict:
    return client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": email, "password": password},
    )


def _actions(db) -> list[str]:
    return list(db.scalars(select(AuditLog.action).order_by(AuditLog.id)))


def _audit_dump(db) -> str:
    entries = db.scalars(select(AuditLog)).all()
    return json.dumps(
        [
            {
                "action": entry.action,
                "resource_id": entry.resource_id,
                "metadata": entry.metadata_json,
            }
            for entry in entries
        ],
        default=str,
    )


def test_failed_login_creates_safe_audit_event(client: TestClient, db_session) -> None:
    user = _create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    submitted = "definitely-not-the-password"

    response = _login(client, user.email, password=submitted)
    assert response.status_code == 401

    db_session.expire_all()
    entry = db_session.scalar(
        select(AuditLog).where(AuditLog.action == AuditAction.AUTH_LOGIN_FAILED)
    )
    assert entry is not None
    assert entry.actor_user_id == user.id
    assert entry.request_id == response.headers.get("X-Request-ID")
    assert entry.metadata_json == {"reason": "invalid_credentials"}

    dump = _audit_dump(db_session)
    assert submitted not in dump
    assert PASSWORD not in dump
    assert "password" not in dump.lower()


def test_successful_login_and_logout_are_audited(client: TestClient, db_session) -> None:
    user = _create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)

    response = _login(client, user.email)
    assert response.status_code == 200
    csrf_token = client.cookies.get(settings.csrf_cookie_name)
    raw_token = client.cookies.get(settings.session_cookie_name)

    db_session.expire_all()
    success = db_session.scalar(
        select(AuditLog).where(AuditLog.action == AuditAction.AUTH_LOGIN_SUCCEEDED)
    )
    assert success is not None
    assert success.actor_user_id == user.id
    assert success.resource_type == "session"
    assert success.resource_id is not None
    assert success.request_id == response.headers.get("X-Request-ID")
    assert success.metadata_json == {"role": "operator"}

    logout = client.post(
        f"{settings.api_v1_prefix}/auth/logout",
        headers={settings.csrf_header_name: csrf_token},
    )
    assert logout.status_code == 204

    db_session.expire_all()
    logout_entry = db_session.scalar(
        select(AuditLog).where(AuditLog.action == AuditAction.AUTH_LOGOUT)
    )
    assert logout_entry is not None
    assert logout_entry.resource_id == success.resource_id

    dump = _audit_dump(db_session)
    assert raw_token not in dump
    assert csrf_token not in dump


def test_password_change_is_audited(client: TestClient, db_session) -> None:
    user = _create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    assert _login(client, user.email).status_code == 200
    csrf_token = client.cookies.get(settings.csrf_cookie_name)

    response = client.post(
        f"{settings.api_v1_prefix}/auth/change-password",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers={settings.csrf_header_name: csrf_token},
    )
    assert response.status_code == 200

    db_session.expire_all()
    entry = db_session.scalar(
        select(AuditLog).where(AuditLog.action == AuditAction.AUTH_PASSWORD_CHANGED)
    )
    assert entry is not None
    assert entry.actor_user_id == user.id

    dump = _audit_dump(db_session)
    assert PASSWORD not in dump
    assert NEW_PASSWORD not in dump


def test_user_administration_creates_audit_events(client: TestClient, db_session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    assert _login(client, admin.email).status_code == 200
    csrf_token = client.cookies.get(settings.csrf_cookie_name)
    headers = {settings.csrf_header_name: csrf_token}

    created = client.post(
        f"{settings.api_v1_prefix}/users",
        json={
            "name": "Field Tech",
            "email": "tech@example.com",
            "password": PASSWORD,
            "role": "operator",
        },
        headers=headers,
    )
    assert created.status_code == 201
    user_id = created.json()["id"]

    assert (
        client.patch(
            f"{settings.api_v1_prefix}/users/{user_id}/status",
            json={"is_active": False},
            headers=headers,
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"{settings.api_v1_prefix}/users/{user_id}",
            json={"role": "technician"},
            headers=headers,
        ).status_code
        == 200
    )

    db_session.expire_all()
    actions = _actions(db_session)
    assert AuditAction.USER_CREATED in actions
    assert AuditAction.USER_STATUS_CHANGED in actions
    assert AuditAction.USER_ROLE_CHANGED in actions
    assert AuditAction.USER_UPDATED in actions

    created_entry = db_session.scalar(
        select(AuditLog).where(AuditLog.action == AuditAction.USER_CREATED)
    )
    assert created_entry.actor_user_id == admin.id
    assert created_entry.resource_type == "user"
    assert created_entry.resource_id == str(user_id)
    assert created_entry.metadata_json == {"role": "operator"}

    status_entry = db_session.scalar(
        select(AuditLog).where(AuditLog.action == AuditAction.USER_STATUS_CHANGED)
    )
    assert status_entry.metadata_json == {"is_active": False}

    role_entry = db_session.scalar(
        select(AuditLog).where(AuditLog.action == AuditAction.USER_ROLE_CHANGED)
    )
    assert role_entry.metadata_json == {"role": "technician"}

    dump = _audit_dump(db_session)
    assert PASSWORD not in dump


def test_audit_log_endpoint_is_admin_only_and_records_access(
    client: TestClient,
    db_session,
) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    assert _login(client, admin.email).status_code == 200

    response = client.get(f"{settings.api_v1_prefix}/audit-logs", params={"limit": 5})
    assert response.status_code == 200
    entries = response.json()
    assert entries
    assert entries[0]["action"] == AuditAction.AUDIT_LOGS_VIEWED
    assert entries[0]["actor_user_id"] == admin.id

    db_session.expire_all()
    assert AuditAction.AUDIT_LOGS_VIEWED in _actions(db_session)


def test_metadata_sanitization_redacts_and_bounds_values() -> None:
    sanitized = sanitize_metadata(
        {
            "password": "super-secret",
            "session_token": "raw-token",
            "csrf_token": "csrf-value",
            "authorization": "Bearer abc",
            "email": "tech@example.com",
            "nested": {"api_key": "key-value", "note": "x" * 500},
            "items": list(range(50)),
        }
    )

    assert sanitized is not None
    assert sanitized["password"] == "[redacted]"
    assert sanitized["session_token"] == "[redacted]"
    assert sanitized["csrf_token"] == "[redacted]"
    assert sanitized["authorization"] == "[redacted]"
    assert sanitized["email"] == "tech@example.com"
    assert sanitized["nested"]["api_key"] == "[redacted]"
    assert len(sanitized["nested"]["note"]) == 200
    assert len(sanitized["items"]) <= 20

    oversized = sanitize_metadata({f"key{index}": "v" * 200 for index in range(20)})
    assert oversized == {"truncated": True, "reason": "metadata_too_large"}

    assert sanitize_metadata({}) is None
    assert sanitize_metadata(None) is None
