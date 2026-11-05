from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.models import UserRole
from tests.helpers import create_user, csrf_headers, login


def test_admin_registers_updates_and_archives_equipment(
    client: TestClient,
    db_session,
) -> None:
    admin = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    csrf = login(client, admin.email)
    prefix = settings.api_v1_prefix

    created = client.post(
        f"{prefix}/equipment",
        json={
            "id": "motor-001",
            "name": "  Press Motor  ",
            "category": "electric_motor",
            "manufacturer": "Example Motors",
            "location": "Line A",
        },
        headers=csrf_headers(csrf),
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["id"] == "motor-001"
    assert body["name"] == "Press Motor"
    assert body["status"] == "active"

    duplicate = client.post(
        f"{prefix}/equipment",
        json={"id": "motor-001", "name": "Duplicate"},
        headers=csrf_headers(csrf),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EQUIPMENT_EXISTS"

    updated = client.patch(
        f"{prefix}/equipment/motor-001",
        json={"name": "Press Motor A", "status": "maintenance"},
        headers=csrf_headers(csrf),
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Press Motor A"
    assert updated.json()["status"] == "maintenance"

    component = client.post(
        f"{prefix}/equipment/motor-001/components",
        json={
            "component_key": "drive_bearing",
            "name": "Drive-end bearing",
            "description": "Prototype component",
        },
        headers=csrf_headers(csrf),
    )
    assert component.status_code == 201, component.text
    component_id = component.json()["id"]

    duplicate_component = client.post(
        f"{prefix}/equipment/motor-001/components",
        json={"component_key": "drive_bearing", "name": "Duplicate"},
        headers=csrf_headers(csrf),
    )
    assert duplicate_component.status_code == 409
    assert duplicate_component.json()["error"]["code"] == "COMPONENT_EXISTS"

    component_update = client.patch(
        f"{prefix}/equipment/motor-001/components/{component_id}",
        json={"name": "Drive bearing"},
        headers=csrf_headers(csrf),
    )
    assert component_update.status_code == 200
    assert component_update.json()["name"] == "Drive bearing"

    archived = client.delete(
        f"{prefix}/equipment/motor-001",
        headers=csrf_headers(csrf),
    )
    assert archived.status_code == 204

    detail = client.get(f"{prefix}/equipment/motor-001")
    assert detail.status_code == 200
    assert detail.json()["status"] == "archived"

    default_list = client.get(f"{prefix}/equipment")
    assert default_list.status_code == 200
    assert default_list.json() == []

    archived_list = client.get(f"{prefix}/equipment", params={"include_archived": "true"})
    assert [item["id"] for item in archived_list.json()] == ["motor-001"]

    components = client.get(f"{prefix}/equipment/motor-001/components")
    assert components.status_code == 200
    assert components.json()[0]["component_key"] == "drive_bearing"

    blocked = client.post(
        f"{prefix}/equipment/motor-001/components",
        json={"component_key": "fan", "name": "Cooling fan"},
        headers=csrf_headers(csrf),
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "EQUIPMENT_ARCHIVED"


def test_equipment_permissions_and_validation(client: TestClient, db_session) -> None:
    admin = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    technician = create_user(db_session, email="tech@example.com", role=UserRole.TECHNICIAN)
    operator = create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    prefix = settings.api_v1_prefix

    created = client.post(
        f"{prefix}/equipment",
        json={"id": "motor-002", "name": "Fan Motor"},
        headers=csrf_headers(login(client, admin.email)),
    )
    assert created.status_code == 201

    with TestClient(app) as technician_client:
        login(technician_client, technician.email)
        assert technician_client.get(f"{prefix}/equipment").status_code == 200
        assert technician_client.get(f"{prefix}/equipment/motor-002").status_code == 200
        forbidden = technician_client.post(
            f"{prefix}/equipment",
            json={"id": "motor-003", "name": "Nope"},
            headers=csrf_headers(technician_client.cookies.get(settings.csrf_cookie_name)),
        )
        assert forbidden.status_code == 403

    with TestClient(app) as operator_client:
        login(operator_client, operator.email)
        assert operator_client.get(f"{prefix}/equipment").status_code == 200
        forbidden = operator_client.delete(
            f"{prefix}/equipment/motor-002",
            headers=csrf_headers(operator_client.cookies.get(settings.csrf_cookie_name)),
        )
        assert forbidden.status_code == 403

    invalid = client.post(
        f"{prefix}/equipment",
        json={"id": "bad id", "name": "Bad"},
        headers=csrf_headers(login(client, admin.email)),
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"

    missing = client.get(f"{prefix}/equipment/missing")
    assert missing.status_code == 404

    null_required = client.patch(
        f"{prefix}/equipment/motor-002",
        json={"name": None},
        headers=csrf_headers(client.cookies.get(settings.csrf_cookie_name)),
    )
    assert null_required.status_code == 400
    assert null_required.json()["error"]["code"] == "VALIDATION_ERROR"
