from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.core.time import utcnow
from app.main import app
from app.models import Alert, AnomalyEvent, SensorReading, UserRole
from app.models.enums import AlertStatus, EquipmentStatus
from tests.helpers import (
    create_user,
    csrf_headers,
    login,
    make_equipment,
    make_reading,
    reading_payload,
)


def test_anomaly_creates_single_alert_and_lifecycle_is_checked(
    client: TestClient,
    db_session,
) -> None:
    make_equipment(db_session)
    technician = create_user(
        db_session,
        email="tech@example.com",
        role=UserRole.TECHNICIAN,
    )
    csrf = login(client, technician.email)
    prefix = settings.api_v1_prefix

    normal = client.post(
        f"{prefix}/readings",
        json=reading_payload(
            "motor-001",
            timestamp=utcnow() - timedelta(seconds=20),
            source_event_id="normal-1",
        ),
    )
    assert normal.status_code == 201

    anomaly = client.post(
        f"{prefix}/readings",
        json=reading_payload(
            "motor-001",
            timestamp=utcnow() - timedelta(seconds=10),
            temperature_c=80.0,
            source_event_id="high-1",
        ),
    )
    assert anomaly.status_code == 201

    db_session.expire_all()
    events = list(db_session.scalars(select(AnomalyEvent)))
    alerts = list(db_session.scalars(select(Alert)))
    assert len(events) == 1
    assert events[0].event_type == "high_temperature"
    assert events[0].end_timestamp is None
    assert len(alerts) == 1
    assert alerts[0].severity == "medium"
    assert alerts[0].status == AlertStatus.OPEN.value
    alert_id = alerts[0].id

    status_response = client.get(f"{prefix}/equipment/motor-001/status")
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["latest_reading"]["temperature_c"] == 80.0
    assert status_body["open_alert_count"] == 1
    assert status_body["is_stale"] is False

    overview = client.get(f"{prefix}/monitoring/overview")
    assert overview.status_code == 200
    assert overview.json()[0]["equipment_id"] == "motor-001"

    listed = client.get(f"{prefix}/alerts", params={"severity": "medium"})
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [alert_id]

    second_anomaly = client.post(
        f"{prefix}/readings",
        json=reading_payload(
            "motor-001",
            timestamp=utcnow() - timedelta(seconds=5),
            temperature_c=82.0,
            source_event_id="high-2",
        ),
    )
    assert second_anomaly.status_code == 201

    db_session.expire_all()
    assert len(list(db_session.scalars(select(AnomalyEvent)))) == 1
    assert len(list(db_session.scalars(select(Alert)))) == 1
    event = db_session.scalar(select(AnomalyEvent))
    assert event is not None
    assert event.end_timestamp is not None

    acknowledged = client.patch(
        f"{prefix}/alerts/{alert_id}/status",
        json={"status": "acknowledged"},
        headers=csrf_headers(csrf),
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"
    assert acknowledged.json()["acknowledged_by"] == technician.id

    resolved = client.patch(
        f"{prefix}/alerts/{alert_id}/status",
        json={"status": "resolved"},
        headers=csrf_headers(csrf),
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved_at"] is not None

    closed = client.patch(
        f"{prefix}/alerts/{alert_id}/status",
        json={"status": "dismissed"},
        headers=csrf_headers(csrf),
    )
    assert closed.status_code == 409
    assert closed.json()["error"]["code"] == "ALERT_CLOSED"

    normal_again = client.post(
        f"{prefix}/readings",
        json=reading_payload(
            "motor-001",
            timestamp=utcnow(),
            temperature_c=55.0,
            source_event_id="normal-2",
        ),
    )
    assert normal_again.status_code == 201

    db_session.expire_all()
    event = db_session.scalar(select(AnomalyEvent))
    assert event is not None
    assert event.end_timestamp is not None


def test_alert_management_requires_technician_or_admin(
    client: TestClient,
    db_session,
) -> None:
    make_equipment(db_session)
    technician = create_user(
        db_session,
        email="tech@example.com",
        role=UserRole.TECHNICIAN,
    )
    login(client, technician.email)
    prefix = settings.api_v1_prefix

    client.post(
        f"{prefix}/readings",
        json=reading_payload(
            "motor-001",
            vibration_value=0.8,
            source_event_id="vibration-1",
        ),
    )
    db_session.expire_all()
    alert = db_session.scalar(select(Alert))
    assert alert is not None

    operator = create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    with TestClient(app) as operator_client:
        operator_csrf = login(operator_client, operator.email)
        forbidden = operator_client.patch(
            f"{prefix}/alerts/{alert.id}/status",
            json={"status": "acknowledged"},
            headers=csrf_headers(operator_csrf),
        )
        assert forbidden.status_code == 403

        visible = operator_client.get(f"{prefix}/alerts/{alert.id}")
        assert visible.status_code == 200

    missing = client.get(f"{prefix}/alerts/999999")
    assert missing.status_code == 404


def test_stale_data_and_archived_overview(client: TestClient, db_session) -> None:
    make_equipment(db_session)
    make_equipment(
        db_session,
        equipment_id="motor-archived",
        status=EquipmentStatus.ARCHIVED,
    )
    make_reading(
        db_session,
        equipment_id="motor-001",
        timestamp=utcnow() - timedelta(minutes=5),
    )
    operator = create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    login(client, operator.email)
    prefix = settings.api_v1_prefix

    status_response = client.get(f"{prefix}/equipment/motor-001/status")
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["is_stale"] is True
    assert body["seconds_since_latest"] >= 300

    overview = client.get(f"{prefix}/monitoring/overview")
    assert overview.status_code == 200
    ids = [item["equipment_id"] for item in overview.json()]
    assert ids == ["motor-001"]

    missing = client.get(f"{prefix}/equipment/missing/status")
    assert missing.status_code == 404

    count = db_session.query(SensorReading).count()
    assert count == 1
