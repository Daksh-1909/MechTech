from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert


def get_alert(db: Session, alert_id: int) -> Alert | None:
    return db.get(Alert, alert_id)


def list_alerts(
    db: Session,
    *,
    status: str | None,
    equipment_id: str | None,
    severity: str | None,
    limit: int,
    offset: int,
) -> list[Alert]:
    statement = select(Alert)
    if status is not None:
        statement = statement.where(Alert.status == status)
    if equipment_id is not None:
        statement = statement.where(Alert.equipment_id == equipment_id)
    if severity is not None:
        statement = statement.where(Alert.severity == severity)
    statement = (
        statement.order_by(Alert.created_at.desc(), Alert.id.desc()).limit(limit).offset(offset)
    )
    return list(db.scalars(statement))
