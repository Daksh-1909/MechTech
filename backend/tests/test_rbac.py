import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.permissions import Permission, has_permission, role_has_permission
from app.models import User, UserRole
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


def _login(client: TestClient, email: str) -> str:
    response = client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 200
    return client.cookies.get(settings.csrf_cookie_name)


def _headers(csrf_token: str) -> dict[str, str]:
    return {settings.csrf_header_name: csrf_token}


def test_role_permission_matrix() -> None:
    assert role_has_permission(UserRole.ADMIN, Permission.USERS_MANAGE)
    assert role_has_permission(UserRole.ADMIN, Permission.AUDIT_VIEW)
    assert role_has_permission(UserRole.ADMIN, Permission.EQUIPMENT_MANAGE)

    assert role_has_permission(UserRole.TECHNICIAN, Permission.ALERTS_MANAGE)
    assert role_has_permission(UserRole.TECHNICIAN, Permission.MAINTENANCE_MANAGE)
    assert not role_has_permission(UserRole.TECHNICIAN, Permission.USERS_MANAGE)
    assert not role_has_permission(UserRole.TECHNICIAN, Permission.AUDIT_VIEW)
    assert not role_has_permission(UserRole.TECHNICIAN, Permission.EQUIPMENT_MANAGE)

    assert role_has_permission(UserRole.OPERATOR, Permission.MONITORING_VIEW)
    assert role_has_permission(UserRole.OPERATOR, Permission.EQUIPMENT_VIEW)
    assert not role_has_permission(UserRole.OPERATOR, Permission.ALERTS_MANAGE)
    assert not role_has_permission(UserRole.OPERATOR, Permission.MAINTENANCE_MANAGE)

    assert not role_has_permission("unknown-role", Permission.MONITORING_VIEW)


def test_inactive_users_have_no_permissions() -> None:
    user = User(
        id=1,
        name="Inactive",
        email="inactive@example.com",
        password_hash="x",
        role=UserRole.ADMIN.value,
        is_active=False,
    )

    assert not has_permission(user, Permission.USERS_MANAGE)


@pytest.mark.parametrize("role", [UserRole.OPERATOR, UserRole.TECHNICIAN])
def test_non_admins_cannot_use_user_administration(
    client: TestClient,
    db_session,
    role: UserRole,
) -> None:
    user = _create_user(db_session, email=f"{role.value}@example.com", role=role)
    csrf_token = _login(client, user.email)

    assert client.get(f"{settings.api_v1_prefix}/users").status_code == 403
    assert client.get(f"{settings.api_v1_prefix}/audit-logs").status_code == 403
    assert (
        client.post(
            f"{settings.api_v1_prefix}/users",
            json={
                "name": "New User",
                "email": "new@example.com",
                "password": PASSWORD,
                "role": "operator",
            },
            headers=_headers(csrf_token),
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"{settings.api_v1_prefix}/users/1/status",
            json={"is_active": False},
            headers=_headers(csrf_token),
        ).status_code
        == 403
    )


def test_admin_can_use_user_administration(client: TestClient, db_session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    operator = _create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    csrf_token = _login(client, admin.email)

    listed = client.get(f"{settings.api_v1_prefix}/users")
    assert listed.status_code == 200
    assert {item["email"] for item in listed.json()} == {admin.email, operator.email}
    assert all("password_hash" not in item for item in listed.json())

    created = client.post(
        f"{settings.api_v1_prefix}/users",
        json={
            "name": "Field Tech",
            "email": " Field.Tech@Example.com ",
            "password": PASSWORD,
            "role": "technician",
        },
        headers=_headers(csrf_token),
    )
    assert created.status_code == 201
    assert created.json()["email"] == "field.tech@example.com"
    assert created.json()["role"] == "technician"

    status = client.patch(
        f"{settings.api_v1_prefix}/users/{created.json()['id']}/status",
        json={"is_active": False},
        headers=_headers(csrf_token),
    )
    assert status.status_code == 200
    assert status.json()["is_active"] is False

    assert client.get(f"{settings.api_v1_prefix}/audit-logs").status_code == 200


def test_permitted_self_access_does_not_leak_other_users(
    client: TestClient,
    db_session,
) -> None:
    operator = _create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    other = _create_user(db_session, email="other@example.com", role=UserRole.OPERATOR)
    csrf_token = _login(client, operator.email)

    own = client.get(f"{settings.api_v1_prefix}/users/{operator.id}")
    assert own.status_code == 200
    assert own.json()["email"] == operator.email

    assert client.get(f"{settings.api_v1_prefix}/users/{other.id}").status_code == 403
    assert client.get(f"{settings.api_v1_prefix}/users/999999").status_code == 403

    updated = client.patch(
        f"{settings.api_v1_prefix}/users/{operator.id}",
        json={"name": "Renamed Operator"},
        headers=_headers(csrf_token),
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Renamed Operator"


def test_role_escalation_is_prevented(client: TestClient, db_session) -> None:
    admin = _create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    operator = _create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    csrf_token = _login(client, operator.email)

    escalation = client.patch(
        f"{settings.api_v1_prefix}/users/{operator.id}",
        json={"role": "admin"},
        headers=_headers(csrf_token),
    )
    assert escalation.status_code == 403
    assert escalation.json()["error"]["code"] == "SELF_ROLE_CHANGE"

    db_session.expire_all()
    assert db_session.get(User, operator.id).role == UserRole.OPERATOR.value

    admin_csrf = _login(client, admin.email)
    self_demotion = client.patch(
        f"{settings.api_v1_prefix}/users/{admin.id}",
        json={"role": "operator"},
        headers=_headers(admin_csrf),
    )
    assert self_demotion.status_code == 403
    assert self_demotion.json()["error"]["code"] == "SELF_ROLE_CHANGE"

    promoted = client.patch(
        f"{settings.api_v1_prefix}/users/{operator.id}",
        json={"role": "technician"},
        headers=_headers(admin_csrf),
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "technician"
