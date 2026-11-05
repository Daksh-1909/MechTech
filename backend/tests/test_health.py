from fastapi.testclient import TestClient


def test_liveness(client: TestClient) -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness(client: TestClient) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_version_does_not_expose_secrets(client: TestClient) -> None:
    response = client.get("/version")
    assert response.status_code == 200

    body = response.json()
    assert body["name"] == "MechTech API"
    assert body["version"] == "0.1.0"
    assert body["api_prefix"] == "/api/v1"
    assert "secret" not in response.text.lower()
    assert "database" not in response.text.lower()


def test_request_id_is_generated(client: TestClient) -> None:
    response = client.get("/health/live")

    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) == 32


def test_request_id_is_propagated(client: TestClient) -> None:
    supplied = "client-request-1234"
    response = client.get("/health/live", headers={"X-Request-ID": supplied})

    assert response.headers.get("X-Request-ID") == supplied


def test_invalid_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "short"})

    returned = response.headers.get("X-Request-ID")
    assert returned is not None
    assert returned != "short"
    assert len(returned) == 32


def test_not_found_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["request_id"] == response.headers.get("X-Request-ID")
    assert "traceback" not in response.text.lower()
