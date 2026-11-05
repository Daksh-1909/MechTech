from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.time import utcnow
from app.main import app
from app.models import SensorReading, UserRole
from tests.helpers import (
    create_user,
    iso,
    login,
    make_equipment,
    reading_payload,
)


def _login_technician(client: TestClient, db_session):
    technician = create_user(
        db_session,
        email="tech@example.com",
        role=UserRole.TECHNICIAN,
    )
    login(client, technician.email)
    return technician


def test_single_and_batch_ingestion_are_idempotent(
    client: TestClient,
    db_session,
) -> None:
    make_equipment(db_session)
    _login_technician(client, db_session)
    prefix = settings.api_v1_prefix
    now = utcnow()

    first = client.post(
        f"{prefix}/readings",
        json=reading_payload("motor-001", timestamp=now, source_event_id="event-1"),
    )
    assert first.status_code == 201, first.text
    assert first.json()["duplicate"] is False
    reading_id = first.json()["reading"]["id"]

    duplicate = client.post(
        f"{prefix}/readings",
        json=reading_payload("motor-001", timestamp=now, source_event_id="event-1"),
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["reading"]["id"] == reading_id

    batch = client.post(
        f"{prefix}/readings/batch",
        json={
            "readings": [
                reading_payload("motor-001", timestamp=now, source_event_id="event-1"),
                reading_payload(
                    "motor-001", timestamp=now + timedelta(seconds=1), source_event_id="event-2"
                ),
                reading_payload(
                    "motor-001", timestamp=now + timedelta(seconds=2), source_event_id="event-2"
                ),
                reading_payload(
                    "motor-001", timestamp=now + timedelta(seconds=3), source_event_id="event-3"
                ),
            ]
        },
    )
    assert batch.status_code == 201, batch.text
    assert batch.json()["created"] == 2
    assert batch.json()["duplicates"] == 2
    assert len(batch.json()["readings"]) == 4

    count = db_session.scalar(select(func.count()).select_from(SensorReading))
    assert count == 3


def test_device_key_allows_unauthenticated_ingestion(
    client: TestClient,
    db_session,
    monkeypatch,
) -> None:
    make_equipment(db_session)
    monkeypatch.setattr(settings, "simulator_api_key", "device-secret")
    prefix = settings.api_v1_prefix
    payload = reading_payload("motor-001", source_event_id="device-event-1")

    with TestClient(app) as anonymous_client:
        rejected = anonymous_client.post(f"{prefix}/readings", json=payload)
        assert rejected.status_code == 401

        wrong = anonymous_client.post(
            f"{prefix}/readings",
            json=payload,
            headers={settings.device_api_key_header: "wrong"},
        )
        assert wrong.status_code == 401

        accepted = anonymous_client.post(
            f"{prefix}/readings",
            json=payload,
            headers={settings.device_api_key_header: "device-secret"},
        )
        assert accepted.status_code == 201, accepted.text


def test_ingestion_validation_and_permissions(client: TestClient, db_session) -> None:
    make_equipment(db_session)
    make_equipment(
        db_session,
        equipment_id="motor-archived",
        status="archived",
    )
    operator = create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    login(client, operator.email)
    prefix = settings.api_v1_prefix
    now = utcnow()

    forbidden = client.post(
        f"{prefix}/readings",
        json=reading_payload("motor-001", timestamp=now),
    )
    assert forbidden.status_code == 403

    with TestClient(app) as anonymous_client:
        missing_auth = anonymous_client.post(
            f"{prefix}/readings",
            json=reading_payload("motor-001", timestamp=now),
        )
        assert missing_auth.status_code == 401

    _login_technician(client, db_session)
    no_channels = client.post(
        f"{prefix}/readings",
        json=reading_payload(
            "motor-001",
            timestamp=now,
            temperature_c=None,
            vibration_value=None,
        ),
    )
    assert no_channels.status_code == 422

    out_of_bounds = client.post(
        f"{prefix}/readings",
        json=reading_payload("motor-001", timestamp=now, temperature_c=500.0),
    )
    assert out_of_bounds.status_code == 422

    bad_unit = client.post(
        f"{prefix}/readings",
        json=reading_payload("motor-001", timestamp=now, vibration_unit="rpm"),
    )
    assert bad_unit.status_code == 422

    future = client.post(
        f"{prefix}/readings",
        json=reading_payload("motor-001", timestamp=now + timedelta(hours=2)),
    )
    assert future.status_code == 422

    missing_equipment = client.post(
        f"{prefix}/readings",
        json=reading_payload("missing-motor", timestamp=now),
    )
    assert missing_equipment.status_code == 404

    archived = client.post(
        f"{prefix}/readings",
        json=reading_payload("motor-archived", timestamp=now),
    )
    assert archived.status_code == 409
    assert archived.json()["error"]["code"] == "EQUIPMENT_ARCHIVED"


def test_historical_queries_are_bounded_and_ordered(
    client: TestClient,
    db_session,
) -> None:
    make_equipment(db_session)
    _login_technician(client, db_session)
    prefix = settings.api_v1_prefix
    now = utcnow()
    start = now - timedelta(hours=3)

    for index, temperature in enumerate((50.0, 55.0, 60.0)):
        response = client.post(
            f"{prefix}/readings",
            json=reading_payload(
                "motor-001",
                timestamp=start + timedelta(hours=index),
                temperature_c=temperature,
                vibration_value=0.1 + index / 10,
                source_event_id=f"history-{index}",
            ),
        )
        assert response.status_code == 201

    response = client.get(
        f"{prefix}/equipment/motor-001/readings",
        params={"from": iso(start), "to": iso(now), "limit": 2},
    )
    assert response.status_code == 200, response.text
    rows = response.json()
    assert len(rows) == 2
    assert [row["temperature_c"] for row in rows] == [50.0, 55.0]

    reversed_range = client.get(
        f"{prefix}/equipment/motor-001/readings",
        params={"from": iso(now), "to": iso(start)},
    )
    assert reversed_range.status_code == 400
    assert reversed_range.json()["error"]["code"] == "INVALID_RANGE"

    too_wide = client.get(
        f"{prefix}/equipment/motor-001/readings",
        params={"from": iso(now - timedelta(days=40)), "to": iso(now)},
    )
    assert too_wide.status_code == 400
    assert too_wide.json()["error"]["code"] == "RANGE_TOO_LARGE"

    too_large = client.get(
        f"{prefix}/equipment/motor-001/readings",
        params={"limit": settings.reading_query_max_limit + 1},
    )
    assert too_large.status_code == 422

    latest = client.get(f"{prefix}/equipment/motor-001/readings/latest")
    assert latest.status_code == 200
    assert latest.json()["temperature_c"] == 60.0

    summary = client.get(
        f"{prefix}/equipment/motor-001/readings/summary",
        params={"from": iso(start), "to": iso(now)},
    )
    assert summary.status_code == 200
    body = summary.json()
    assert body["count"] == 3
    assert body["temperature_min"] == 50.0
    assert body["temperature_max"] == 60.0
    assert round(body["temperature_avg"], 2) == 55.0

    missing = client.get(f"{prefix}/equipment/missing/readings")
    assert missing.status_code == 404

    make_equipment(db_session, equipment_id="motor-empty")
    no_latest = client.get(f"{prefix}/equipment/motor-empty/readings/latest")
    assert no_latest.status_code == 404
