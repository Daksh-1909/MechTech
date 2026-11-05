from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.time import utcnow
from app.models import Alert, User
from app.models.enums import AlertStatus
from app.modules.alerts import repository
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction

_TERMINAL_STATUSES = {AlertStatus.RESOLVED.value, AlertStatus.DISMISSED.value}

_ACTION_BY_STATUS = {
    AlertStatus.ACKNOWLEDGED.value: AuditAction.ALERT_ACKNOWLEDGED,
    AlertStatus.RESOLVED.value: AuditAction.ALERT_RESOLVED,
    AlertStatus.DISMISSED.value: AuditAction.ALERT_DISMISSED,
}


def get_alert(db: Session, alert_id: int) -> Alert:
    alert = repository.get_alert(db, alert_id)
    if alert is None:
        raise AppError("Alert not found.", code="NOT_FOUND", status_code=404)
    return alert


def list_alerts(
    db: Session,
    *,
    status: str | None,
    equipment_id: str | None,
    severity: str | None,
    limit: int,
    offset: int,
) -> list[Alert]:
    return repository.list_alerts(
        db,
        status=status,
        equipment_id=equipment_id,
        severity=severity,
        limit=limit,
        offset=offset,
    )


def update_alert_status(
    db: Session,
    *,
    actor: User,
    alert_id: int,
    new_status: AlertStatus,
) -> Alert:
    alert = get_alert(db, alert_id)
    target = new_status.value

    if alert.status == target:
        return alert

    if alert.status in _TERMINAL_STATUSES:
        raise AppError(
            "The alert is already closed.",
            code="ALERT_CLOSED",
            status_code=409,
        )

    if target == AlertStatus.OPEN.value:
        raise AppError(
            "An alert cannot be reopened.",
            code="INVALID_STATUS_TRANSITION",
            status_code=409,
        )

    alert.status = target
    if target == AlertStatus.ACKNOWLEDGED.value:
        alert.acknowledged_by = actor.id
    if target == AlertStatus.RESOLVED.value:
        alert.resolved_at = utcnow()
        if alert.acknowledged_by is None:
            alert.acknowledged_by = actor.id

    audit_service.record_event(
        db,
        action=_ACTION_BY_STATUS[target],
        resource_type="alert",
        resource_id=alert.id,
        actor_user_id=actor.id,
        metadata={"equipment_id": alert.equipment_id, "status": target},
    )
    db.commit()
    db.refresh(alert)
    return alert
