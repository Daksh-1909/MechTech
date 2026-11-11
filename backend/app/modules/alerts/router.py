from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.core.permissions import Permission
from app.models import User
from app.models.enums import AlertStatus, Severity
from app.modules.alerts import service
from app.modules.alerts.schemas import (
    AlertActionRequest,
    AlertResponse,
    AlertStatusUpdateRequest,
)
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    require_permission,
)

router = APIRouter()

AlertManager = Annotated[User, Depends(require_permission(Permission.ALERT_ACKNOWLEDGE))]


@router.get("", response_model=list[AlertResponse], tags=["alerts"])
def list_alerts(
    db: DbSession,
    user: CurrentUser,
    organization_id: uuid.UUID | None = None,
    equipment_id: uuid.UUID | None = None,
    status: AlertStatus | None = None,
    severity: Severity | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AlertResponse]:
    alerts = service.list_alerts(
        db,
        actor=user,
        organization_id=organization_id,
        equipment_id=equipment_id,
        status=None if status is None else status.value,
        severity=None if severity is None else severity.value,
        limit=limit,
        offset=offset,
    )
    return [AlertResponse.model_validate(a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertResponse, tags=["alerts"])
def get_alert(
    alert_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> AlertResponse:
    alert = service.get_alert(db, actor=user, alert_id=alert_id)
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse, tags=["alerts"])
def acknowledge_alert(
    alert_id: uuid.UUID,
    db: DbSession,
    manager: AlertManager,
    _: CsrfProtected,
    payload: AlertActionRequest | None = None,
) -> AlertResponse:
    note = payload.note if payload else None
    alert = service.acknowledge_alert(db, actor=manager, alert_id=alert_id, note=note)
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/resolve", response_model=AlertResponse, tags=["alerts"])
def resolve_alert(
    alert_id: uuid.UUID,
    db: DbSession,
    manager: AlertManager,
    _: CsrfProtected,
    payload: AlertActionRequest | None = None,
) -> AlertResponse:
    note = payload.note if payload else None
    alert = service.resolve_alert(db, actor=manager, alert_id=alert_id, note=note)
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/dismiss", response_model=AlertResponse, tags=["alerts"])
def dismiss_alert(
    alert_id: uuid.UUID,
    db: DbSession,
    manager: AlertManager,
    _: CsrfProtected,
    payload: AlertActionRequest | None = None,
) -> AlertResponse:
    note = payload.note if payload else None
    alert = service.dismiss_alert(db, actor=manager, alert_id=alert_id, note=note)
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}/status", response_model=AlertResponse, tags=["alerts"])
def update_alert_status(
    alert_id: uuid.UUID,
    payload: AlertStatusUpdateRequest,
    db: DbSession,
    manager: AlertManager,
    _: CsrfProtected,
) -> AlertResponse:
    alert = service.update_alert_status(
        db,
        actor=manager,
        alert_id=alert_id,
        new_status=payload.status,
        note=payload.note,
    )
    return AlertResponse.model_validate(alert)
