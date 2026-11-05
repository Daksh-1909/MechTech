from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.time import utcnow
from app.main import app
from app.models import UserRole
from tests.helpers import create_user, iso, login


def test_domain_endpoints_require_authentication() -> None:
    prefix = settings.api_v1_prefix
    paths = [
        "/equipment",
        "/equipment/motor-001",
        "/equipment/motor-001/components",
        "/equipment/motor-001/readings",
        "/equipment/motor-001/readings/latest",
        "/equipment/motor-001/readings/summary",
        "/monitoring/overview",
        "/equipment/motor-001/status",
        "/alerts",
        "/alerts/1",
        "/predictions",
        "/predictions/1",
        "/models",
        "/knowledge-graph",
        "/knowledge-graph/nodes/1",
        "/knowledge-graph/nodes/1/neighbors",
        "/maintenance-records",
        "/maintenance-records/1",
    ]

    with TestClient(app) as anonymous_client:
        for path in paths:
            response = anonymous_client.get(f"{prefix}{path}")
            assert response.status_code == 401, path
            body = response.json()
            assert body["error"]["code"] == "UNAUTHORIZED"
            assert body["error"]["request_id"] == response.headers["X-Request-ID"]


def test_all_state_changing_domain_endpoints_require_csrf(
    client: TestClient,
    db_session,
) -> None:
    admin = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    login(client, admin.email)
    prefix = settings.api_v1_prefix

    maintenance_payload = {
        "equipment_id": "motor-001",
        "inspection_timestamp": iso(utcnow()),
        "outcome": "pending_verification",
        "verification_status": "pending",
    }
    cases = [
        ("POST", "/equipment", {"id": "motor-x", "name": "Motor X"}),
        ("PATCH", "/equipment/motor-x", {"name": "Motor Y"}),
        ("DELETE", "/equipment/motor-x", None),
        (
            "POST",
            "/equipment/motor-x/components",
            {"component_key": "bearing", "name": "Bearing"},
        ),
        (
            "PATCH",
            "/equipment/motor-x/components/1",
            {"name": "Bearing"},
        ),
        ("PATCH", "/alerts/1/status", {"status": "acknowledged"}),
        ("POST", "/equipment/motor-x/analysis", {}),
        (
            "POST",
            "/knowledge-graph/nodes",
            {"node_type": "fault", "stable_key": "fault:x", "label": "Fault X"},
        ),
        (
            "POST",
            "/knowledge-graph/edges",
            {
                "source_node_id": 1,
                "target_node_id": 2,
                "relationship_type": "AFFECTS",
            },
        ),
        ("PATCH", "/knowledge-graph/nodes/1", {"label": "Updated"}),
        ("POST", "/maintenance-records", maintenance_payload),
        ("PATCH", "/maintenance-records/1", {"notes": "Updated"}),
    ]

    for method, path, payload in cases:
        response = client.request(method, f"{prefix}{path}", json=payload)
        assert response.status_code == 403, (method, path, response.text)
        assert response.json()["error"]["code"] == "CSRF_FAILED"


def test_settings_secrets_are_not_exposed(
    client: TestClient,
    monkeypatch,
) -> None:
    secret = "super-secret-device-key"
    monkeypatch.setattr(settings, "simulator_api_key", secret)

    version = client.get("/version")
    assert version.status_code == 200
    assert secret not in version.text
    assert "simulator_api_key" not in version.text

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    assert secret not in openapi.text
    assert "password_hash" not in openapi.text
    assert "token_hash" not in openapi.text
