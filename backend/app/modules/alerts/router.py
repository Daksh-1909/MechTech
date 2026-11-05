from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.core.permissions import Permission
from app.models import User
from app.models.enums import AlertStatus, Severity
from app.modules.alerts import service
from app.modules.alerts.schemas import AlertResponse, AlertStatusUpdateRequest
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    require_permission,
)

router = APIRouter()

AlertManager = Annotated[User, Depends(require_permission(Permission.ALERTS_MANAGE))]


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    db: DbSession,
    user: CurrentUser,
    status: AlertStatus | None = None,
    equipment_id: str | None = None,
    severity: Severity | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AlertResponse]:
    alerts = service.list_alerts(
        db,
        status=None if status is None else status.value,
        equipment_id=equipment_id,
        severity=None if severity is None else severity.value,
        limit=limit,
        offset=offset,
    )
    return [AlertResponse.model_validate(alert) for alert in alerts]


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: DbSession, user: CurrentUser) -> AlertResponse:
    return AlertResponse.model_validate(service.get_alert(db, alert_id))


@router.patch("/{alert_id}/status", response_model=AlertResponse)
def update_alert_status(
    alert_id: int,
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
    )
    return AlertResponse.model_validate(alert)
