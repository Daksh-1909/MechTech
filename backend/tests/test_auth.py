from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import hash_token
from app.core.time import utcnow
from app.models import User, UserRole, UserSession
from app.modules.auth import service

PASSWORD = "correct-horse-battery"
NEW_PASSWORD = "battery-staple-horse"
EMAIL = "tech@example.com"


def _create_user(
    db,
    *,
    email: str = EMAIL,
    password: str = PASSWORD,
    role: UserRole = UserRole.TECHNICIAN,
) -> User:
    return service.create_user(db, name="Test Tech", email=email, password=password, role=role)


def _login(client: TestClient, *, email: str = EMAIL, password: str = PASSWORD):
    return client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": email, "password": password},
    )


def _csrf(client: TestClient) -> str:
    return client.cookies.get(settings.csrf_cookie_name)


def _session_for(db, raw_token: str) -> UserSession:
    return db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(raw_token)))


def test_login_sets_cookies_and_returns_user(client: TestClient, db_session) -> None:
    _create_user(db_session)

    response = _login(client, email="  TECH@Example.com ")

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == EMAIL
    assert body["user"]["role"] == "technician"
    assert body["csrf_token"]
    assert body["expires_at"]

    raw_session = client.cookies.get(settings.session_cookie_name)
    assert raw_session
    assert client.cookies.get(settings.csrf_cookie_name) == body["csrf_token"]

    set_cookie_headers = response.headers.get_list("set-cookie")
    session_header = next(
        header for header in set_cookie_headers if header.startswith(settings.session_cookie_name)
    )
    csrf_header = next(
        header for header in set_cookie_headers if header.startswith(settings.csrf_cookie_name)
    )
    assert "HttpOnly" in session_header
    assert "HttpOnly" not in csrf_header

    stored = _session_for(db_session, raw_session)
    assert stored is not None
    assert stored.token_hash != raw_session
    assert len(stored.token_hash) == 64
    assert stored.csrf_token_hash != body["csrf_token"]
    assert stored.csrf_token_hash == hash_token(body["csrf_token"])
    assert stored.revoked_at is None


def test_invalid_credentials_do_not_disclose_account_state(client: TestClient, db_session) -> None:
    _create_user(db_session)

    wrong_password = _login(client, password="wrong-password-here")
    unknown_email = _login(client, email="nobody@example.com")

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert wrong_password.json()["error"]["message"] == unknown_email.json()["error"]["message"]


def test_me_requires_an_active_session(client: TestClient, db_session) -> None:
    _create_user(db_session)

    assert client.get(f"{settings.api_v1_prefix}/auth/me").status_code == 401

    assert _login(client).status_code == 200
    response = client.get(f"{settings.api_v1_prefix}/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == EMAIL


def test_logout_requires_csrf_and_revokes_session(client: TestClient, db_session) -> None:
    _create_user(db_session)
    assert _login(client).status_code == 200
    raw_session = client.cookies.get(settings.session_cookie_name)
    csrf_token = _csrf(client)

    missing = client.post(f"{settings.api_v1_prefix}/auth/logout")
    assert missing.status_code == 403
    assert missing.json()["error"]["code"] == "CSRF_FAILED"

    wrong = client.post(
        f"{settings.api_v1_prefix}/auth/logout",
        headers={settings.csrf_header_name: "not-the-token"},
    )
    assert wrong.status_code == 403

    response = client.post(
        f"{settings.api_v1_prefix}/auth/logout",
        headers={settings.csrf_header_name: csrf_token},
    )
    assert response.status_code == 204
    assert settings.session_cookie_name not in client.cookies

    db_session.expire_all()
    stored = _session_for(db_session, raw_session)
    assert stored is not None
    assert stored.revoked_at is not None
    assert client.get(f"{settings.api_v1_prefix}/auth/me").status_code == 401


def test_expired_and_revoked_sessions_are_rejected(client: TestClient, db_session) -> None:
    _create_user(db_session)
    assert _login(client).status_code == 200
    raw_session = client.cookies.get(settings.session_cookie_name)

    stored = _session_for(db_session, raw_session)
    stored.expires_at = utcnow() - timedelta(seconds=1)
    db_session.commit()

    assert client.get(f"{settings.api_v1_prefix}/auth/me").status_code == 401


def test_inactive_user_sessions_are_rejected(client: TestClient, db_session) -> None:
    user = _create_user(db_session)
    assert _login(client).status_code == 200

    user.is_active = False
    db_session.commit()

    assert client.get(f"{settings.api_v1_prefix}/auth/me").status_code == 401


def test_origin_is_validated_on_unsafe_requests(client: TestClient, db_session) -> None:
    _create_user(db_session)

    rejected = client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        headers={"origin": "https://evil.example"},
    )
    assert rejected.status_code == 403
    assert rejected.json()["error"]["code"] == "CSRF_FAILED"

    accepted = client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        headers={"origin": "http://localhost:5173"},
    )
    assert accepted.status_code == 200


def test_change_password_revokes_other_sessions(client: TestClient, db_session) -> None:
    _create_user(db_session)

    assert _login(client).status_code == 200
    first_token = client.cookies.get(settings.session_cookie_name)

    assert _login(client).status_code == 200
    second_token = client.cookies.get(settings.session_cookie_name)
    csrf_token = _csrf(client)

    missing_csrf = client.post(
        f"{settings.api_v1_prefix}/auth/change-password",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert missing_csrf.status_code == 403

    wrong_current = client.post(
        f"{settings.api_v1_prefix}/auth/change-password",
        json={"current_password": "not-the-password", "new_password": NEW_PASSWORD},
        headers={settings.csrf_header_name: csrf_token},
    )
    assert wrong_current.status_code == 400
    assert wrong_current.json()["error"]["code"] == "INVALID_PASSWORD"

    unchanged = client.post(
        f"{settings.api_v1_prefix}/auth/change-password",
        json={"current_password": PASSWORD, "new_password": PASSWORD},
        headers={settings.csrf_header_name: csrf_token},
    )
    assert unchanged.status_code == 400
    assert unchanged.json()["error"]["code"] == "PASSWORD_UNCHANGED"

    response = client.post(
        f"{settings.api_v1_prefix}/auth/change-password",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers={settings.csrf_header_name: csrf_token},
    )
    assert response.status_code == 200

    db_session.expire_all()
    assert _session_for(db_session, first_token).revoked_at is not None
    assert _session_for(db_session, second_token).revoked_at is None
    assert client.get(f"{settings.api_v1_prefix}/auth/me").status_code == 200

    assert _login(client, password=PASSWORD).status_code == 401
    assert _login(client, password=NEW_PASSWORD).status_code == 200


def test_sessions_can_be_listed_and_revoked(client: TestClient, db_session) -> None:
    _create_user(db_session)

    assert _login(client).status_code == 200
    first_id = _session_for(db_session, client.cookies.get(settings.session_cookie_name)).id

    assert _login(client).status_code == 200
    current_id = _session_for(db_session, client.cookies.get(settings.session_cookie_name)).id
    csrf_token = _csrf(client)

    listed = client.get(f"{settings.api_v1_prefix}/auth/sessions")
    assert listed.status_code == 200
    sessions = listed.json()
    assert {item["id"] for item in sessions} == {first_id, current_id}
    assert {item["id"] for item in sessions if item["is_current"]} == {current_id}

    response = client.delete(
        f"{settings.api_v1_prefix}/auth/sessions/{first_id}",
        headers={settings.csrf_header_name: csrf_token},
    )
    assert response.status_code == 204

    db_session.expire_all()
    stored = db_session.get(UserSession, first_id)
    assert stored.revoked_at is not None

    missing = client.delete(
        f"{settings.api_v1_prefix}/auth/sessions/999999",
        headers={settings.csrf_header_name: csrf_token},
    )
    assert missing.status_code == 404


def test_protected_endpoints_require_authentication(client: TestClient) -> None:
    prefix = settings.api_v1_prefix
    assert client.get(f"{prefix}/auth/me").status_code == 401
    assert client.get(f"{prefix}/auth/sessions").status_code == 401
    assert client.delete(f"{prefix}/auth/sessions/1").status_code in {401, 403}
    assert client.post(
        f"{prefix}/auth/change-password",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
    ).status_code in {401, 403}


def test_initial_admin_can_only_be_created_once(db_session) -> None:
    _create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)

    admin = service.create_initial_admin(
        db_session,
        name="Admin",
        email=" Admin@Example.com ",
        password=PASSWORD,
    )
    assert admin.role == UserRole.ADMIN
    assert admin.email == "admin@example.com"
    assert admin.password_hash != PASSWORD

    with pytest.raises(AppError) as exc_info:
        service.create_initial_admin(
            db_session,
            name="Second Admin",
            email="second@example.com",
            password=PASSWORD,
        )
    assert exc_info.value.code == "ADMIN_EXISTS"


def test_duplicate_email_and_weak_password_are_rejected(db_session) -> None:
    _create_user(db_session)

    with pytest.raises(AppError) as exc_info:
        _create_user(db_session, email="TECH@example.com")
    assert exc_info.value.code == "EMAIL_IN_USE"

    with pytest.raises(AppError) as exc_info:
        _create_user(db_session, email="short@example.com", password="too-short")
    assert exc_info.value.code == "WEAK_PASSWORD"
