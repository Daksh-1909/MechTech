from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.time import utcnow
from app.models import Sensor


def create_sensor(
    db: Session,
    *,
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    sensor_key: str,
    measurement_type: str,
    unit: str,
    component_id: uuid.UUID | None = None,
    status: str = "active",
    configuration: dict[str, Any] | None = None,
) -> Sensor:
    sensor = Sensor(
        organization_id=organization_id,
        equipment_id=equipment_id,
        component_id=component_id,
        sensor_key=sensor_key,
        measurement_type=measurement_type,
        unit=unit,
        status=status,
        configuration=configuration,
    )
    db.add(sensor)
    db.flush()
    return sensor


def get_sensor_by_id(db: Session, sensor_id: uuid.UUID | str) -> Sensor | None:
    sid = sensor_id if isinstance(sensor_id, uuid.UUID) else uuid.UUID(str(sensor_id))
    return db.scalar(
        select(Sensor)
        .options(
            joinedload(Sensor.equipment),
            joinedload(Sensor.component),
            joinedload(Sensor.organization),
        )
        .where(Sensor.id == sid)
    )


def get_sensor_by_key(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    sensor_key: str,
) -> Sensor | None:
    return db.scalar(
        select(Sensor).where(
            Sensor.equipment_id == equipment_id,
            Sensor.sensor_key == sensor_key,
        )
    )


def list_sensors(
    db: Session,
    *,
    equipment_id: uuid.UUID | str | None = None,
    organization_id: uuid.UUID | str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Sensor]:
    stmt = (
        select(Sensor)
        .options(joinedload(Sensor.component))
        .order_by(Sensor.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    if equipment_id is not None:
        eid = equipment_id if isinstance(equipment_id, uuid.UUID) else uuid.UUID(str(equipment_id))
        stmt = stmt.where(Sensor.equipment_id == eid)
    if organization_id is not None:
        oid = organization_id if isinstance(organization_id, uuid.UUID) else uuid.UUID(str(organization_id))
        stmt = stmt.where(Sensor.organization_id == oid)
    return list(db.scalars(stmt))


def update_sensor(
    db: Session,
    *,
    sensor_id: uuid.UUID | str,
    changes: dict[str, Any],
) -> Sensor | None:
    sid = sensor_id if isinstance(sensor_id, uuid.UUID) else uuid.UUID(str(sensor_id))
    sensor = db.get(Sensor, sid)
    if not sensor:
        return None
    for field, value in changes.items():
        if hasattr(sensor, field) and field not in {"id", "equipment_id", "organization_id", "created_at"}:
            setattr(sensor, field, value)
    sensor.updated_at = utcnow()
    db.flush()
    return sensor
