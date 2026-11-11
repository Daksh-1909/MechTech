"""Repository for SensorReading persistence and queries.

Keeps reading concerns separate from sensor-entity CRUD in repository.py.
"""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.time import utcnow
from app.models import SensorReading
from app.models.enums import ReadingQuality


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


def create_reading(
    db: Session,
    *,
    organization_id: uuid.UUID,
    equipment_id: uuid.UUID,
    sensor_id: uuid.UUID | None,
    timestamp: datetime,
    temperature_c: float | None,
    vibration_value: float | None,
    vibration_unit: str,
    value: float | None,
    unit: str | None,
    source: str,
    source_event_id: str | None,
    schema_version: str,
    sequence_number: int | None,
    speed_rpm: float | None,
    load_percent: float | None,
    scenario_id: str | None,
    scenario_label: str | None,
    simulation_seed: int | None,
    simulation_run_id: str | None,
    quality_status: str = ReadingQuality.VALID.value,
    metadata_json: dict[str, Any] | None = None,
) -> SensorReading:
    """Persist a single reading.  Caller must flush/commit."""
    reading = SensorReading(
        organization_id=organization_id,
        equipment_id=equipment_id,
        sensor_id=sensor_id,
        timestamp=timestamp,
        received_at=utcnow(),
        temperature_c=temperature_c,
        vibration_value=vibration_value,
        vibration_unit=vibration_unit,
        value=value,
        unit=unit,
        source=source,
        source_event_id=source_event_id,
        schema_version=schema_version,
        sequence_number=sequence_number,
        speed_rpm=speed_rpm,
        load_percent=load_percent,
        scenario_id=scenario_id,
        scenario_label=scenario_label,
        simulation_seed=simulation_seed,
        simulation_run_id=simulation_run_id,
        quality_status=quality_status,
        metadata_json=metadata_json,
    )
    db.add(reading)
    db.flush()
    return reading


def get_reading_by_event_id(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    source: str,
    source_event_id: str,
) -> SensorReading | None:
    """Look up an existing reading by its idempotency triple."""
    return db.scalar(
        select(SensorReading).where(
            SensorReading.equipment_id == equipment_id,
            SensorReading.source == source,
            SensorReading.source_event_id == source_event_id,
        )
    )


def get_reading_by_sensor_event_id(
    db: Session,
    *,
    sensor_id: uuid.UUID,
    source_event_id: str,
) -> SensorReading | None:
    """Look up an existing reading by sensor and idempotency key."""
    return db.scalar(
        select(SensorReading).where(
            SensorReading.sensor_id == sensor_id,
            SensorReading.source_event_id == source_event_id,
        )
    )


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def list_readings(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
    before_id: uuid.UUID | None = None,
) -> list[SensorReading]:
    """Return readings for equipment in descending timestamp order.

    ``before_id`` enables keyset / cursor pagination: pass the ``id`` of the
    last reading returned to fetch the next page.
    """
    stmt = (
        select(SensorReading)
        .where(SensorReading.equipment_id == equipment_id)
        .order_by(SensorReading.timestamp.desc(), SensorReading.id.desc())
        .limit(limit)
    )
    if start is not None:
        stmt = stmt.where(SensorReading.timestamp >= start)
    if end is not None:
        stmt = stmt.where(SensorReading.timestamp <= end)
    if before_id is not None:
        anchor = db.scalar(select(SensorReading.timestamp).where(SensorReading.id == before_id))
        if anchor is not None:
            stmt = stmt.where(SensorReading.timestamp < anchor)
    return list(db.scalars(stmt))


def list_readings_by_sensor(
    db: Session,
    *,
    sensor_id: uuid.UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
    before_id: uuid.UUID | None = None,
) -> list[SensorReading]:
    """Return readings for a specific sensor in descending timestamp order."""
    stmt = (
        select(SensorReading)
        .where(SensorReading.sensor_id == sensor_id)
        .order_by(SensorReading.timestamp.desc(), SensorReading.id.desc())
        .limit(limit)
    )
    if start is not None:
        stmt = stmt.where(SensorReading.timestamp >= start)
    if end is not None:
        stmt = stmt.where(SensorReading.timestamp <= end)
    if before_id is not None:
        anchor = db.scalar(select(SensorReading.timestamp).where(SensorReading.id == before_id))
        if anchor is not None:
            stmt = stmt.where(SensorReading.timestamp < anchor)
    return list(db.scalars(stmt))


def get_latest_reading(
    db: Session,
    *,
    equipment_id: uuid.UUID,
) -> SensorReading | None:
    return db.scalar(
        select(SensorReading)
        .where(SensorReading.equipment_id == equipment_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(1)
    )


def summarize_readings(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict[str, Any]:
    """Return aggregate statistics over the requested window.

    Returns a plain dict so the service layer can build the response schema.
    """
    stmt = select(
        func.count(SensorReading.id).label("count"),
        func.min(SensorReading.temperature_c).label("temperature_min"),
        func.max(SensorReading.temperature_c).label("temperature_max"),
        func.avg(SensorReading.temperature_c).label("temperature_avg"),
        func.min(SensorReading.vibration_value).label("vibration_min"),
        func.max(SensorReading.vibration_value).label("vibration_max"),
        func.avg(SensorReading.vibration_value).label("vibration_avg"),
    ).where(SensorReading.equipment_id == equipment_id)
    if start is not None:
        stmt = stmt.where(SensorReading.timestamp >= start)
    if end is not None:
        stmt = stmt.where(SensorReading.timestamp <= end)

    row = db.execute(stmt).one()
    return {
        "count": row.count or 0,
        "temperature_min": row.temperature_min,
        "temperature_max": row.temperature_max,
        "temperature_avg": float(row.temperature_avg) if row.temperature_avg is not None else None,
        "vibration_min": row.vibration_min,
        "vibration_max": row.vibration_max,
        "vibration_avg": float(row.vibration_avg) if row.vibration_avg is not None else None,
    }

