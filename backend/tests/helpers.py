from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utcnow
from app.models import Equipment, SensorReading, User, UserRole
from app.models.enums import EquipmentStatus
from app.modules.auth import service

PASSWORD = "correct-horse-battery"


def create_user(
    db: Session,
    *,
    email: str,
    role: UserRole = UserRole.OPERATOR,
    name: str | None = None,
) -> User:
    return service.create_user(
        db,
        name=name or f"{role.value.title()} User",
        email=email,
        password=PASSWORD,
        role=role,
    )


def login(client: TestClient, email: str, password: str = PASSWORD) -> str:
    response = client.post(
        f"{settings.api_v1_prefix}/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return client.cookies.get(settings.csrf_cookie_name)


def csrf_headers(csrf_token: str | None) -> dict[str, str]:
    assert csrf_token is not None
    return {settings.csrf_header_name: csrf_token}


def make_equipment(
    db: Session,
    *,
    equipment_id: str = "motor-001",
    name: str = "Test Motor",
    status: EquipmentStatus | str = EquipmentStatus.ACTIVE,
) -> Equipment:
    equipment = Equipment(
        id=equipment_id,
        name=name,
        category="electric_motor",
        status=getattr(status, "value", status),
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


def make_reading(
    db: Session,
    *,
    equipment_id: str = "motor-001",
    timestamp: datetime | None = None,
    temperature_c: float | None = 50.0,
    vibration_value: float | None = 0.2,
    source: str = "test",
    source_event_id: str | None = None,
) -> SensorReading:
    reading = SensorReading(
        equipment_id=equipment_id,
        timestamp=timestamp or utcnow(),
        received_at=utcnow(),
        temperature_c=temperature_c,
        vibration_value=vibration_value,
        vibration_unit="simulated_index",
        source=source,
        source_event_id=source_event_id,
        quality_status="valid",
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def reading_payload(
    equipment_id: str,
    *,
    timestamp: datetime | None = None,
    temperature_c: float | None = 50.0,
    vibration_value: float | None = 0.2,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "equipment_id": equipment_id,
        "timestamp": iso(timestamp or utcnow()),
        "temperature_c": temperature_c,
        "vibration_value": vibration_value,
    }
    payload.update(extra)
    return payload
