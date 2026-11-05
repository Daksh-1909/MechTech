from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MaintenanceRecord


def get_record(db: Session, record_id: int) -> MaintenanceRecord | None:
    return db.get(MaintenanceRecord, record_id)


def list_records(
    db: Session,
    *,
    equipment_id: str | None,
    outcome: str | None,
    limit: int,
    offset: int,
) -> list[MaintenanceRecord]:
    statement = select(MaintenanceRecord)
    if equipment_id is not None:
        statement = statement.where(MaintenanceRecord.equipment_id == equipment_id)
    if outcome is not None:
        statement = statement.where(MaintenanceRecord.outcome == outcome)
    statement = (
        statement.order_by(
            MaintenanceRecord.inspection_timestamp.desc(),
            MaintenanceRecord.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement))
