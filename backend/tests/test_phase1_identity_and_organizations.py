import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models import Organization, OrganizationMember, Role, User, UserRoleAssignment, UserStatus
from app.modules.auth import service as auth_service
from app.modules.organizations import service as org_service

PASSWORD = "correct-horse-battery"
ADMIN_PASSWORD = "admin-strong-password-123"


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


def _create_platform_admin(db) -> User:
    auth_service.repository.ensure_default_roles_and_permissions(db)
    admin = auth_service.repository.get_user_by_email(db, "platform_admin@example.com")
    if not admin:
        admin = auth_service.create_user(
            db,
            name="Platform Admin",
            email="platform_admin@example.com",
            password=ADMIN_PASSWORD,
            role="platform_admin",
            status=UserStatus.ACTIVE.value,
        )
    return admin


def test_public_registration_creates_pending_account_and_blocks_login(client: TestClient, db_session) -> None:
    _create_platform_admin(db_session)

    # 1. Public user submits registration
    reg_response = client.post(
        f"{settings.api_v1_prefix}/auth/register",
        json={
            "email": "new.tech@example.com",
            "password": PASSWORD,
            "display_name": "New Technician",
            "organization_name": "Acme Industries",
        },
    )
    assert reg_response.status_code == 201
    body = reg_response.json()
    assert body["status"] == "pending"
    assert "user_id" in body

    # 2. Pending user cannot log in
    status_code, login_body, _ = _login(client, "new.tech@example.com", PASSWORD)
    assert status_code == 403
    assert login_body["error"]["code"] == "ACCOUNT_PENDING"

    # 3. Protected endpoint cannot be accessed
    me_response = client.get(f"{settings.api_v1_prefix}/auth/me")
    assert me_response.status_code == 401


def test_admin_approves_registration_flow(client: TestClient, db_session) -> None:
    admin = _create_platform_admin(db_session)
    status_code, _, admin_csrf = _login(client, admin.email, ADMIN_PASSWORD)
    assert status_code == 200

    # Create an organization for assignment
    org = org_service.create_organization(
        db_session,
        actor=admin,
        name="Reliability Corp",
        slug="reliability-corp",
    )

    # Public user registers
    client.post(
        f"{settings.api_v1_prefix}/auth/register",
        json={
            "email": "operator.bob@example.com",
            "password": PASSWORD,
            "display_name": "Operator Bob",
        },
    )

    # Admin lists pending registrations
    list_res = client.get(
        f"{settings.api_v1_prefix}/admin/registrations",
        headers=_headers(admin_csrf),
    )
    assert list_res.status_code == 200
    registrations = list_res.json()
    assert len(registrations) >= 1
    target_req = next(r for r in registrations if r["email"] == "operator.bob@example.com")
    assert target_req["status"] == "pending"

    # Admin approves registration
    approve_res = client.post(
        f"{settings.api_v1_prefix}/admin/registrations/{target_req['id']}/approve",
        json={
            "organization_id": str(org.id),
            "role_key": "maintainer",
            "review_note": "Approved for Workshop 3",
        },
        headers=_headers(admin_csrf),
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"

    # Now Bob logs in
    bob_client = TestClient(client.app)
    bob_status, bob_body, _ = _login(bob_client, "operator.bob@example.com", PASSWORD)
    assert bob_status == 200
    assert bob_body["user"]["status"] == "active"
    assert "maintainer" in bob_body["user"]["roles"]

    # Verify /auth/me returns membership and permissions
    me_res = bob_client.get(f"{settings.api_v1_prefix}/auth/me")
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "operator.bob@example.com"
    assert any(o["slug"] == "reliability-corp" for o in me_data["organizations"])
    assert "maintenance.create" in me_data["permissions"]


def test_admin_rejects_registration_flow(client: TestClient, db_session) -> None:
    admin = _create_platform_admin(db_session)
    status_code, _, admin_csrf = _login(client, admin.email, ADMIN_PASSWORD)
    assert status_code == 200

    # User registers
    client.post(
        f"{settings.api_v1_prefix}/auth/register",
        json={
            "email": "suspicious@example.com",
            "password": PASSWORD,
            "display_name": "Suspicious User",
        },
    )

    list_res = client.get(
        f"{settings.api_v1_prefix}/admin/registrations",
        headers=_headers(admin_csrf),
    )
    target_req = next(r for r in list_res.json() if r["email"] == "suspicious@example.com")

    # Reject
    reject_res = client.post(
        f"{settings.api_v1_prefix}/admin/registrations/{target_req['id']}/reject",
        json={"review_note": "Unverified external domain"},
        headers=_headers(admin_csrf),
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "rejected"

    # Attempt login -> blocked
    rej_status, rej_body, _ = _login(client, "suspicious@example.com", PASSWORD)
    assert rej_status == 403
    assert rej_body["error"]["code"] == "ACCOUNT_INACTIVE"


def test_admin_directly_creates_user(client: TestClient, db_session) -> None:
    admin = _create_platform_admin(db_session)
    status_code, _, admin_csrf = _login(client, admin.email, ADMIN_PASSWORD)
    assert status_code == 200

    create_res = client.post(
        f"{settings.api_v1_prefix}/admin/users",
        json={
            "name": "Direct User",
            "email": "direct.user@example.com",
            "password": PASSWORD,
            "role": "viewer",
        },
        headers=_headers(admin_csrf),
    )
    assert create_res.status_code == 201
    assert create_res.json()["status"] == "active"

    # User logs in directly without approval
    u_status, u_data, _ = _login(client, "direct.user@example.com", PASSWORD)
    assert u_status == 200
    assert u_data["user"]["is_active"] is True


def test_cross_organization_data_isolation(client: TestClient, db_session) -> None:
    admin = _create_platform_admin(db_session)
    _, _, admin_csrf = _login(client, admin.email, ADMIN_PASSWORD)

    # 1. Create Organization Alpha and Organization Beta
    org_alpha = org_service.create_organization(
        db_session,
        actor=admin,
        name="Alpha Org",
        slug="alpha-org",
    )
    org_beta = org_service.create_organization(
        db_session,
        actor=admin,
        name="Beta Org",
        slug="beta-org",
    )

    # 2. Create User Alpha belonging only to Alpha Org
    user_alpha = auth_service.create_user(
        db_session,
        name="Alpha Technician",
        email="tech.alpha@example.com",
        password=PASSWORD,
        role="maintainer",
        organization_id=org_alpha.id,
    )

    # 3. Create User Beta belonging only to Beta Org
    user_beta = auth_service.create_user(
        db_session,
        name="Beta Technician",
        email="tech.beta@example.com",
        password=PASSWORD,
        role="maintainer",
        organization_id=org_beta.id,
    )

    # User Alpha logs in
    alpha_client = TestClient(client.app)
    a_status, _, _ = _login(alpha_client, user_alpha.email, PASSWORD)
    assert a_status == 200

    # User Alpha lists organizations -> should only see Alpha Org
    alpha_orgs = alpha_client.get(f"{settings.api_v1_prefix}/organizations").json()
    assert len(alpha_orgs) == 1
    assert alpha_orgs[0]["slug"] == "alpha-org"

    # User Alpha attempts to access Beta Org directly -> blocked with 403 Forbidden
    beta_access = alpha_client.get(f"{settings.api_v1_prefix}/organizations/{org_beta.id}")
    assert beta_access.status_code == 403

    # User Beta logs in
    beta_client = TestClient(client.app)
    b_status, _, _ = _login(beta_client, user_beta.email, PASSWORD)
    assert b_status == 200

    # User Beta attempts to access Alpha Org directly -> blocked with 403 Forbidden
    alpha_access = beta_client.get(f"{settings.api_v1_prefix}/organizations/{org_alpha.id}")
    assert alpha_access.status_code == 403

