from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.main import app
from app.models import User, UserRole, UserSession
from app.modules.auth import service

PASSWORD = "correct-horse-battery"


def _create_user(db, *, email: str, role: UserRole) -> User:
    return service.create_user(
        db,
        name=f"{role.value.title()} User",
        email=email,
        password=PASSWORD,
        role=role,
    )


def _login(client: TestClient, email: str, password: str = PASSWORD) -> str | None:
    response = client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": email, "password": password},
    )
    if response.status_code != 200:
        return None
    return client.cookies.get(settings.csrf_cookie_name)


def _headers(csrf_token: str) -> dict[str, str]:
    return {settings.csrf_header_name: csrf_token}


def test_admin_creates_user_with_normalized_fields(client: TestClient, db_session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    csrf_token = _login(client, admin.email)

    response = client.post(
        f"{settings.api_v1_prefix}/users",
        json={
            "name": "  Maintenance Tech  ",
            "email": "  TECH@Example.COM ",
            "password": PASSWORD,
            "role": "technician",
        },
        headers=_headers(csrf_token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Maintenance Tech"
    assert body["email"] == "tech@example.com"
    assert body["role"] == "technician"
    assert body["is_active"] is True
    assert "password_hash" not in body
    assert "password" not in body

    db_session.expire_all()
    stored = db_session.scalar(select(User).where(User.email == "tech@example.com"))
    assert stored is not None
    assert stored.password_hash != PASSWORD


def test_duplicate_email_and_weak_password_are_rejected(
    client: TestClient,
    db_session,
) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    existing = _create_user(db_session, email="existing@example.com", role=UserRole.OPERATOR)
    csrf_token = _login(client, admin.email)

    duplicate = client.post(
        f"{settings.api_v1_prefix}/users",
        json={
            "name": "Duplicate",
            "email": existing.email.upper(),
            "password": PASSWORD,
            "role": "operator",
        },
        headers=_headers(csrf_token),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_IN_USE"

    weak = client.post(
        f"{settings.api_v1_prefix}/users",
        json={
            "name": "Weak",
            "email": "weak@example.com",
            "password": "too-short",
            "role": "operator",
        },
        headers=_headers(csrf_token),
    )
    assert weak.status_code == 422
    assert weak.json()["error"]["code"] == "VALIDATION_ERROR"

    missing_csrf = client.post(
        f"{settings.api_v1_prefix}/users",
        json={
            "name": "No CSRF",
            "email": "nocsrf@example.com",
            "password": PASSWORD,
            "role": "operator",
        },
    )
    assert missing_csrf.status_code == 403


def test_admin_updates_email_and_rejects_conflicts(client: TestClient, db_session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    first = _create_user(db_session, email="first@example.com", role=UserRole.OPERATOR)
    second = _create_user(db_session, email="second@example.com", role=UserRole.OPERATOR)
    csrf_token = _login(client, admin.email)

    updated = client.patch(
        f"{settings.api_v1_prefix}/users/{first.id}",
        json={"email": " First.New@Example.com "},
        headers=_headers(csrf_token),
    )
    assert updated.status_code == 200
    assert updated.json()["email"] == "first.new@example.com"

    conflict = client.patch(
        f"{settings.api_v1_prefix}/users/{first.id}",
        json={"email": second.email},
        headers=_headers(csrf_token),
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "EMAIL_IN_USE"

    null_field = client.patch(
        f"{settings.api_v1_prefix}/users/{first.id}",
        json={"name": None},
        headers=_headers(csrf_token),
    )
    assert null_field.status_code == 400
    assert null_field.json()["error"]["code"] == "VALIDATION_ERROR"

    unknown = client.patch(
        f"{settings.api_v1_prefix}/users/00000000-0000-0000-0000-000000000000",
        json={"name": "Nobody"},
        headers=_headers(csrf_token),
    )
    assert unknown.status_code == 404


def test_non_admin_cannot_probe_user_ids(client: TestClient, db_session) -> None:
    operator = _create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    csrf_token = _login(client, operator.email)

    existing = client.patch(
        f"{settings.api_v1_prefix}/users/11111111-1111-1111-1111-111111111111",
        json={"name": "Probe"},
        headers=_headers(csrf_token),
    )
    missing = client.patch(
        f"{settings.api_v1_prefix}/users/00000000-0000-0000-0000-000000000000",
        json={"name": "Probe"},
        headers=_headers(csrf_token),
    )

    assert existing.status_code == 403
    assert missing.status_code == 403


def test_role_change_revokes_target_sessions(client: TestClient, db_session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    operator = _create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)

    with TestClient(app) as operator_client:
        assert _login(operator_client, operator.email) is not None
        assert operator_client.get(f"{settings.api_v1_prefix}/auth/me").status_code == 200

        csrf_token = _login(client, admin.email)
        updated = client.patch(
            f"{settings.api_v1_prefix}/users/{operator.id}",
            json={"role": "technician"},
            headers=_headers(csrf_token),
        )
        assert updated.status_code == 200
        assert updated.json()["role"] == "technician"

        assert operator_client.get(f"{settings.api_v1_prefix}/auth/me").status_code == 401

    db_session.expire_all()
    session = db_session.scalar(select(UserSession).where(UserSession.user_id == operator.id))
    assert session.revoked_at is not None


def test_deactivation_revokes_sessions_and_blocks_login(
    client: TestClient,
    db_session,
) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    operator = _create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)

    with TestClient(app) as operator_client:
        assert _login(operator_client, operator.email) is not None

        csrf_token = _login(client, admin.email)
        response = client.patch(
            f"{settings.api_v1_prefix}/users/{operator.id}/status",
            json={"is_active": False},
            headers=_headers(csrf_token),
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

        assert operator_client.get(f"{settings.api_v1_prefix}/auth/me").status_code == 401

    assert _login(client, operator.email) is None
    assert (
        client.post(
            f"{settings.api_v1_prefix}/auth/login",
            json={"email": operator.email, "password": PASSWORD},
        ).json()["error"]["code"]
        == "INVALID_CREDENTIALS"
    )


def test_admin_cannot_deactivate_self(client: TestClient, db_session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    csrf_token = _login(client, admin.email)

    response = client.patch(
        f"{settings.api_v1_prefix}/users/{admin.id}/status",
        json={"is_active": False},
        headers=_headers(csrf_token),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SELF_DEACTIVATION"


def test_user_list_is_paginated(client: TestClient, db_session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    for index in range(3):
        _create_user(db_session, email=f"user{index}@example.com", role=UserRole.OPERATOR)
    _login(client, admin.email)

    first_page = client.get(
        f"{settings.api_v1_prefix}/users",
        params={"limit": 2, "offset": 0},
    )
    second_page = client.get(
        f"{settings.api_v1_prefix}/users",
        params={"limit": 2, "offset": 2},
    )

    assert first_page.status_code == 200
    assert len(first_page.json()) == 2
    assert len(second_page.json()) == 2
    assert {item["id"] for item in first_page.json()}.isdisjoint(
        {item["id"] for item in second_page.json()}
    )

    invalid = client.get(
        f"{settings.api_v1_prefix}/users",
        params={"limit": 1000},
    )
    assert invalid.status_code == 422
