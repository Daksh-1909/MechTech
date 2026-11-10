import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models import User, UserStatus
from app.modules.auth import service as auth_service
from app.modules.equipment import repository as eq_repo
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


def _setup_test_context(db):
    auth_service.repository.ensure_default_roles_and_permissions(db)
    eq_repo.ensure_default_equipment_types(db)

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

    org_a = org_service.create_organization(db, actor=admin, name="Industrial Alpha", slug="industrial-alpha")
    org_b = org_service.create_organization(db, actor=admin, name="Industrial Beta", slug="industrial-beta")

    maintainer_a = auth_service.create_user(
        db,
        name="Maintainer Alpha",
        email="maintainer.a@example.com",
        password=PASSWORD,
        role="maintainer",
        organization_id=org_a.id,
    )

    maintainer_b = auth_service.create_user(
        db,
        name="Maintainer Beta",
        email="maintainer.b@example.com",
        password=PASSWORD,
        role="maintainer",
        organization_id=org_b.id,
    )

    return admin, org_a, org_b, maintainer_a, maintainer_b


def test_equipment_type_registry(client: TestClient, db_session) -> None:
    admin, _, _, _, _ = _setup_test_context(db_session)
    status_code, _, admin_csrf = _login(client, admin.email, ADMIN_PASSWORD)
    assert status_code == 200

    res = client.get(f"{settings.api_v1_prefix}/equipment/types", headers=_headers(admin_csrf))
    assert res.status_code == 200
    types = res.json()
    assert any(t["key"] == "electric_motor" for t in types)


def test_create_electric_motor_with_specifications(client: TestClient, db_session) -> None:
    _, org_a, _, maintainer_a, _ = _setup_test_context(db_session)
    status_code, _, csrf_token = _login(client, maintainer_a.email, PASSWORD)
    assert status_code == 200

    motor_payload = {
        "organization_id": str(org_a.id),
        "equipment_type_key": "electric_motor",
        "asset_tag": "MTR-2026-001",
        "name": "Primary Conveyor Motor",
        "manufacturer": "Siemens",
        "model_number": "1LE1001-1DB2",
        "serial_number": "SN-987654321",
        "location_label": "Building C, Line 2",
        "status": "operational",
        "specification": {
            "rated_power_kw": 15.0,
            "rated_voltage_v": 400.0,
            "rated_current_a": 28.5,
            "rated_speed_rpm": 1465.0,
            "frequency_hz": 50.0,
            "phase_count": 3,
            "motor_type": "three_phase_induction",
            "frame_size": "160M",
            "insulation_class": "F",
        },
    }

    create_res = client.post(
        f"{settings.api_v1_prefix}/equipment",
        json=motor_payload,
        headers=_headers(csrf_token),
    )
    assert create_res.status_code == 201
    motor = create_res.json()
    assert motor["name"] == "Primary Conveyor Motor"
    assert motor["asset_tag"] == "MTR-2026-001"
    assert motor["specification"]["rated_power_kw"] == 15.0
    assert motor["specification"]["motor_type"] == "three_phase_induction"
    assert motor["status"] == "operational"

    # Duplicate asset tag in same organization must fail
    dup_res = client.post(
        f"{settings.api_v1_prefix}/equipment",
        json=motor_payload,
        headers=_headers(csrf_token),
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "ASSET_TAG_IN_USE"


def test_component_hierarchy_and_validation(client: TestClient, db_session) -> None:
    _, org_a, _, maintainer_a, _ = _setup_test_context(db_session)
    _, _, csrf_token = _login(client, maintainer_a.email, PASSWORD)

    # 1. Create Motor
    motor = client.post(
        f"{settings.api_v1_prefix}/equipment",
        json={
            "organization_id": str(org_a.id),
            "name": "Extruder Drive Motor",
            "asset_tag": "MTR-EXT-01",
        },
        headers=_headers(csrf_token),
    ).json()
    motor_id = motor["id"]

    # 2. Add Parent Component (Motor Housing/Frame)
    housing_res = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/components",
        json={
            "component_key": "stator_housing",
            "name": "Stator Housing Frame",
            "component_type": "housing",
            "description": "Cast iron motor frame with cooling fins",
        },
        headers=_headers(csrf_token),
    )
    assert housing_res.status_code == 201
    housing = housing_res.json()
    assert housing["component_key"] == "stator_housing"

    # 3. Add Sub-component with valid Parent
    bearing_res = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/components",
        json={
            "component_key": "bearing_front",
            "name": "Front Drive End Bearing",
            "component_type": "bearing",
            "parent_component_id": housing["id"],
            "manufacturer": "SKF",
            "model_number": "6309-2Z",
        },
        headers=_headers(csrf_token),
    )
    assert bearing_res.status_code == 201
    bearing = bearing_res.json()
    assert bearing["parent_component_id"] == housing["id"]

    # 4. Duplicate component key on same equipment fails
    dup_res = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/components",
        json={
            "component_key": "bearing_front",
            "name": "Duplicate Bearing",
        },
        headers=_headers(csrf_token),
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "COMPONENT_KEY_IN_USE"

    # 5. Invalid parent component ID fails
    invalid_parent_res = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/components",
        json={
            "component_key": "bearing_rear",
            "name": "Rear Bearing",
            "parent_component_id": str(uuid.uuid4()),
        },
        headers=_headers(csrf_token),
    )
    assert invalid_parent_res.status_code == 400
    assert invalid_parent_res.json()["error"]["code"] == "INVALID_PARENT_COMPONENT"


def test_sensor_registration_and_component_mapping(client: TestClient, db_session) -> None:
    _, org_a, _, maintainer_a, _ = _setup_test_context(db_session)
    _, _, csrf_token = _login(client, maintainer_a.email, PASSWORD)

    # 1. Create Motor & Bearing Component
    motor_id = client.post(
        f"{settings.api_v1_prefix}/equipment",
        json={"organization_id": str(org_a.id), "name": "Pump Motor A"},
        headers=_headers(csrf_token),
    ).json()["id"]

    bearing_id = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/components",
        json={"component_key": "de_bearing", "name": "Drive-end Bearing"},
        headers=_headers(csrf_token),
    ).json()["id"]

    # 2. Register Temperature Sensor mapped to Bearing
    temp_sensor_res = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/sensors",
        json={
            "sensor_key": "temp_de_bearing",
            "measurement_type": "temperature",
            "unit": "°C",
            "component_id": bearing_id,
            "configuration": {"min_range": -20.0, "max_range": 150.0, "sample_rate_hz": 1},
        },
        headers=_headers(csrf_token),
    )
    assert temp_sensor_res.status_code == 201
    sensor = temp_sensor_res.json()
    assert sensor["sensor_key"] == "temp_de_bearing"
    assert sensor["unit"] == "°C"
    assert sensor["component_id"] == bearing_id

    # 3. Register Vibration Sensor
    vib_sensor_res = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/sensors",
        json={
            "sensor_key": "vib_de_bearing",
            "measurement_type": "vibration",
            "unit": "mm/s",
            "component_id": bearing_id,
            "configuration": {"scale": "velocity_rms"},
        },
        headers=_headers(csrf_token),
    )
    assert vib_sensor_res.status_code == 201

    # 4. List sensors for equipment
    sensors_list = client.get(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/sensors",
        headers=_headers(csrf_token),
    ).json()
    assert len(sensors_list) == 2

    # 5. Duplicate sensor key fails
    dup_sensor = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/sensors",
        json={
            "sensor_key": "temp_de_bearing",
            "measurement_type": "temperature",
            "unit": "°C",
        },
        headers=_headers(csrf_token),
    )
    assert dup_sensor.status_code == 409
    assert dup_sensor.json()["error"]["code"] == "SENSOR_KEY_IN_USE"


def test_equipment_assignment_flow(client: TestClient, db_session) -> None:
    _, org_a, org_b, maintainer_a, maintainer_b = _setup_test_context(db_session)
    _, _, csrf_token = _login(client, maintainer_a.email, PASSWORD)

    motor_id = client.post(
        f"{settings.api_v1_prefix}/equipment",
        json={"organization_id": str(org_a.id), "name": "Blower Motor"},
        headers=_headers(csrf_token),
    ).json()["id"]

    # Assign maintainer_a (same org) -> succeeds
    assign_res = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/assignments",
        json={
            "user_id": str(maintainer_a.id),
            "assignment_type": "primary_maintainer",
        },
        headers=_headers(csrf_token),
    )
    assert assign_res.status_code == 201
    assert assign_res.json()["user_id"] == str(maintainer_a.id)

    # Assign user from foreign org -> fails
    cross_assign_res = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/assignments",
        json={
            "user_id": str(maintainer_b.id),
            "assignment_type": "inspector",
        },
        headers=_headers(csrf_token),
    )
    assert cross_assign_res.status_code == 400
    assert cross_assign_res.json()["error"]["code"] == "INVALID_USER_ORGANIZATION"


def test_cross_tenant_equipment_isolation(client: TestClient, db_session) -> None:
    _, org_a, org_b, maintainer_a, maintainer_b = _setup_test_context(db_session)

    # 1. Maintainer A creates equipment in Org A
    _, _, csrf_a = _login(client, maintainer_a.email, PASSWORD)
    motor_a = client.post(
        f"{settings.api_v1_prefix}/equipment",
        json={"organization_id": str(org_a.id), "name": "Motor A Only"},
        headers=_headers(csrf_a),
    ).json()

    # 2. Maintainer B logs in
    client_b = TestClient(client.app)
    _, _, csrf_b = _login(client_b, maintainer_b.email, PASSWORD)

    # Maintainer B lists equipment -> does not see Motor A
    list_b = client_b.get(f"{settings.api_v1_prefix}/equipment").json()
    assert not any(item["id"] == motor_a["id"] for item in list_b)

    # Maintainer B attempts to access Motor A directly -> 403 Forbidden
    direct_access = client_b.get(f"{settings.api_v1_prefix}/equipment/{motor_a['id']}")
    assert direct_access.status_code == 403

    # Maintainer B attempts to add a component to Motor A -> 403 Forbidden
    comp_attempt = client_b.post(
        f"{settings.api_v1_prefix}/equipment/{motor_a['id']}/components",
        json={"component_key": "illegal_comp", "name": "Illegal Component"},
        headers=_headers(csrf_b),
    )
    assert comp_attempt.status_code == 403


def test_soft_archival_of_equipment(client: TestClient, db_session) -> None:
    _, org_a, _, maintainer_a, _ = _setup_test_context(db_session)
    _, _, csrf_token = _login(client, maintainer_a.email, PASSWORD)

    motor = client.post(
        f"{settings.api_v1_prefix}/equipment",
        json={"organization_id": str(org_a.id), "name": "Retiring Motor"},
        headers=_headers(csrf_token),
    ).json()
    motor_id = motor["id"]

    # Archive equipment
    archive_res = client.post(
        f"{settings.api_v1_prefix}/equipment/{motor_id}/archive",
        headers=_headers(csrf_token),
    )
    assert archive_res.status_code == 200
    assert archive_res.json()["status"] == "archived"

    # Listing active equipment excludes archived by default
    active_list = client.get(f"{settings.api_v1_prefix}/equipment").json()
    assert not any(item["id"] == motor_id for item in active_list)

    # Listing with include_archived=true includes it
    all_list = client.get(
        f"{settings.api_v1_prefix}/equipment",
        params={"include_archived": True},
    ).json()
    assert any(item["id"] == motor_id for item in all_list)

