from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.core.permissions import Permission
from app.models import User
from app.models.enums import MaintenanceOutcome
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    require_permission,
)
from app.modules.maintenance import service
from app.modules.maintenance.schemas import (
    MaintenanceCreateRequest,
    MaintenanceResponse,
    MaintenanceUpdateRequest,
)

router = APIRouter()

MaintenanceWriter = Annotated[
    User,
    Depends(require_permission(Permission.MAINTENANCE_MANAGE)),
]


@router.get("", response_model=list[MaintenanceResponse])
def list_records(
    db: DbSession,
    user: CurrentUser,
    equipment_id: str | None = None,
    outcome: MaintenanceOutcome | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[MaintenanceResponse]:
    records = service.list_records(
        db,
        equipment_id=equipment_id,
        outcome=None if outcome is None else outcome.value,
        limit=limit,
        offset=offset,
    )
    return [MaintenanceResponse.model_validate(record) for record in records]


@router.post("", response_model=MaintenanceResponse, status_code=201)
def create_record(
    payload: MaintenanceCreateRequest,
    db: DbSession,
    technician: MaintenanceWriter,
    _: CsrfProtected,
) -> MaintenanceResponse:
    record = service.create_record(db, actor=technician, values=payload.model_dump())
    return MaintenanceResponse.model_validate(record)


@router.get("/{record_id}", response_model=MaintenanceResponse)
def get_record(record_id: int, db: DbSession, user: CurrentUser) -> MaintenanceResponse:
    return MaintenanceResponse.model_validate(service.get_record(db, record_id))


@router.patch("/{record_id}", response_model=MaintenanceResponse)
def update_record(
    record_id: int,
    payload: MaintenanceUpdateRequest,
    db: DbSession,
    actor: CurrentUser,
    _: CsrfProtected,
) -> MaintenanceResponse:
    record = service.update_record(
        db,
        actor=actor,
        record_id=record_id,
        changes=payload.model_dump(exclude_unset=True),
    )
    return MaintenanceResponse.model_validate(record)
