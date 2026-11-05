from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import SensorReading


def get_reading(db: Session, reading_id: int) -> SensorReading | None:
    return db.get(SensorReading, reading_id)


def get_by_event_id(
    db: Session,
    *,
    equipment_id: str,
    source: str,
    source_event_id: str,
) -> SensorReading | None:
    return db.scalar(
        select(SensorReading).where(
            SensorReading.equipment_id == equipment_id,
            SensorReading.source == source,
            SensorReading.source_event_id == source_event_id,
        )
    )


def get_by_sequence(
    db: Session,
    *,
    equipment_id: str,
    sequence_number: int,
) -> SensorReading | None:
    return db.scalar(
        select(SensorReading).where(
            SensorReading.equipment_id == equipment_id,
            SensorReading.sequence_number == sequence_number,
        )
    )


def get_latest_reading(db: Session, equipment_id: str) -> SensorReading | None:
    return db.scalar(
        select(SensorReading)
        .where(SensorReading.equipment_id == equipment_id)
        .order_by(SensorReading.timestamp.desc(), SensorReading.id.desc())
        .limit(1)
    )


def list_readings(
    db: Session,
    *,
    equipment_id: str,
    start: datetime | None,
    end: datetime | None,
    limit: int,
) -> list[SensorReading]:
    statement = select(SensorReading).where(SensorReading.equipment_id == equipment_id)
    if start is not None:
        statement = statement.where(SensorReading.timestamp >= start)
    if end is not None:
        statement = statement.where(SensorReading.timestamp <= end)
    statement = statement.order_by(SensorReading.timestamp.asc(), SensorReading.id.asc()).limit(
        limit
    )
    return list(db.scalars(statement))


def list_recent_readings(
    db: Session,
    *,
    equipment_id: str,
    limit: int,
) -> list[SensorReading]:
    readings = list(
        db.scalars(
            select(SensorReading)
            .where(SensorReading.equipment_id == equipment_id)
            .order_by(SensorReading.timestamp.desc(), SensorReading.id.desc())
            .limit(limit)
        )
    )
    readings.reverse()
    return readings


def summarize_readings(
    db: Session,
    *,
    equipment_id: str,
    start: datetime | None,
    end: datetime | None,
) -> dict:
    statement = select(
        func.count(SensorReading.id),
        func.min(SensorReading.timestamp),
        func.max(SensorReading.timestamp),
        func.min(SensorReading.temperature_c),
        func.max(SensorReading.temperature_c),
        func.avg(SensorReading.temperature_c),
        func.min(SensorReading.vibration_value),
        func.max(SensorReading.vibration_value),
        func.avg(SensorReading.vibration_value),
    ).where(SensorReading.equipment_id == equipment_id)
    if start is not None:
        statement = statement.where(SensorReading.timestamp >= start)
    if end is not None:
        statement = statement.where(SensorReading.timestamp <= end)

    row = db.execute(statement).one()
    return {
        "count": row[0] or 0,
        "from_timestamp": row[1],
        "to_timestamp": row[2],
        "temperature_min": row[3],
        "temperature_max": row[4],
        "temperature_avg": row[5],
        "vibration_min": row[6],
        "vibration_max": row[7],
        "vibration_avg": row[8],
    }


def create_reading(db: Session, **values) -> SensorReading:
    reading = SensorReading(**values)
    db.add(reading)
    db.flush()
    return reading
