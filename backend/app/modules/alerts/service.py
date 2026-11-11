"""Alerts service: alert lifecycle management and audit logging."""

from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.core.time import utcnow
from app.models import Alert, User
from app.models.enums import AlertStatus
from app.modules.alerts import repository
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.equipment import service as eq_service

_TERMINAL_STATUSES = {AlertStatus.RESOLVED.value, AlertStatus.DISMISSED.value}

_ACTION_BY_STATUS = {
    AlertStatus.ACKNOWLEDGED.value: AuditAction.ALERT_ACKNOWLEDGED,
    AlertStatus.RESOLVED.value: AuditAction.ALERT_RESOLVED,
    AlertStatus.DISMISSED.value: AuditAction.ALERT_DISMISSED,
}


def _is_platform_admin(user: User) -> bool:
    return any(
        a.role and a.role.key in {"platform_admin", "admin"}
        for a in getattr(user, "assigned_roles", [])
    )


def get_alert(db: Session, actor: User, alert_id: uuid.UUID | str) -> Alert:
    alert = repository.get_alert_by_id(db, alert_id)
    if alert is None:
        raise AppError("Alert not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == alert.organization_id for m in memberships):
            raise AppError("Access denied to this alert.", code="FORBIDDEN", status_code=403)

    return alert


def list_alerts(
    db: Session,
    *,
    actor: User,
    organization_id: uuid.UUID | str | None = None,
    equipment_id: uuid.UUID | str | None = None,
    status: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Alert]:
    target_org_id = None
    if organization_id:
        target_org_id = eq_service.resolve_organization_for_actor(actor, organization_id)
    elif not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if memberships:
            target_org_id = memberships[0].organization_id

    eid = None
    if equipment_id:
        eq = eq_service.get_equipment(db, actor, equipment_id)
        eid = eq.id

    return repository.list_alerts(
        db,
        organization_id=target_org_id,
        equipment_id=eid,
        status=status,
        severity=severity,
        limit=limit,
        offset=offset,
    )


def update_alert_status(
    db: Session,
    *,
    actor: User,
    alert_id: uuid.UUID | str,
    new_status: str | AlertStatus,
    note: str | None = None,
) -> Alert:
    alert = get_alert(db, actor, alert_id)
    target = new_status.value if hasattr(new_status, "value") else str(new_status)

    if alert.status == target:
        return alert

    if alert.status in _TERMINAL_STATUSES:
        raise AppError("The alert is already closed.", code="ALERT_CLOSED", status_code=409)

    if target == AlertStatus.OPEN.value:
        raise AppError("An alert cannot be reopened.", code="INVALID_STATUS_TRANSITION", status_code=409)

    # Permission check per target status
    perm_map = {
        AlertStatus.ACKNOWLEDGED.value: Permission.ALERT_ACKNOWLEDGE,
        AlertStatus.RESOLVED.value: Permission.ALERT_RESOLVE,
        AlertStatus.DISMISSED.value: Permission.ALERT_DISMISS,
    }
    required_perm = perm_map.get(target, Permission.ALERT_ACKNOWLEDGE)
    if not _is_platform_admin(actor) and not has_permission(actor, required_perm, organization_id=alert.organization_id):
        raise AppError(f"Permission denied to transition alert to '{target}'.", code="FORBIDDEN", status_code=403)

    updated = repository.update_alert_status(
        db,
        alert_id=alert.id,
        new_status=target,
        actor_id=actor.id,
        note=note,
    )

    action = _ACTION_BY_STATUS.get(target, AuditAction.ALERT_ACKNOWLEDGED)
    audit_service.record_event(
        db,
        action=action,
        resource_type="alert",
        resource_id=alert.id,
        actor_user_id=actor.id,
        organization_id=alert.organization_id,
        metadata={"equipment_id": str(alert.equipment_id), "status": target, "note": note},
    )
    db.commit()
    db.refresh(updated)
    return updated


def acknowledge_alert(
    db: Session,
    *,
    actor: User,
    alert_id: uuid.UUID | str,
    note: str | None = None,
) -> Alert:
    return update_alert_status(
        db,
        actor=actor,
        alert_id=alert_id,
        new_status=AlertStatus.ACKNOWLEDGED,
        note=note,
    )


def resolve_alert(
    db: Session,
    *,
    actor: User,
    alert_id: uuid.UUID | str,
    note: str | None = None,
) -> Alert:
    return update_alert_status(
        db,
        actor=actor,
        alert_id=alert_id,
        new_status=AlertStatus.RESOLVED,
        note=note,
    )


def dismiss_alert(
    db: Session,
    *,
    actor: User,
    alert_id: uuid.UUID | str,
    note: str | None = None,
) -> Alert:
    return update_alert_status(
        db,
        actor=actor,
        alert_id=alert_id,
        new_status=AlertStatus.DISMISSED,
        note=note,
    )
