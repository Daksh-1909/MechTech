from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.api.deps import DbSession
from app.core.permissions import Permission
from app.models import User
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    require_permission,
)
from app.modules.files import service as file_service
from app.modules.files.schemas import StoredFileResponse
from app.modules.maintenance import service
from app.modules.maintenance.schemas import (
    MaintenanceRecordCreate,
    MaintenanceRecordResponse,
    MaintenanceRecordUpdate,
    MaintenanceVerifyRequest,
)

router = APIRouter()

MaintenanceCreator = Annotated[
    User,
    Depends(require_permission(Permission.MAINTENANCE_CREATE)),
]
MaintenanceUpdater = Annotated[
    User,
    Depends(require_permission(Permission.MAINTENANCE_UPDATE)),
]
MaintenanceVerifier = Annotated[
    User,
    Depends(require_permission(Permission.MAINTENANCE_VERIFY)),
]
FileUploader = Annotated[
    User,
    Depends(require_permission(Permission.FILES_UPLOAD)),
]


@router.get("", response_model=list[MaintenanceRecordResponse], tags=["maintenance"])
def list_records(
    db: DbSession,
    user: CurrentUser,
    organization_id: uuid.UUID | None = None,
    equipment_id: uuid.UUID | None = None,
    status: str | None = None,
    priority: str | None = None,
    outcome: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[MaintenanceRecordResponse]:
    return service.list_records(
        db,
        actor=user,
        organization_id=organization_id,
        equipment_id=equipment_id,
        status=status,
        priority=priority,
        outcome=outcome,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=MaintenanceRecordResponse, status_code=201, tags=["maintenance"])
def create_record(
    payload: MaintenanceRecordCreate,
    db: DbSession,
    actor: MaintenanceCreator,
    _: CsrfProtected,
) -> MaintenanceRecordResponse:
    return service.create_record(db, actor=actor, payload=payload)


@router.get("/{record_id}", response_model=MaintenanceRecordResponse, tags=["maintenance"])
def get_record(
    record_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> MaintenanceRecordResponse:
    return service.get_record(db, actor=user, record_id=record_id)


@router.patch("/{record_id}", response_model=MaintenanceRecordResponse, tags=["maintenance"])
def update_record(
    record_id: uuid.UUID,
    payload: MaintenanceRecordUpdate,
    db: DbSession,
    actor: MaintenanceUpdater,
    _: CsrfProtected,
) -> MaintenanceRecordResponse:
    return service.update_record(db, actor=actor, record_id=record_id, payload=payload)


@router.post("/{record_id}/verify", response_model=MaintenanceRecordResponse, tags=["maintenance"])
def verify_record(
    record_id: uuid.UUID,
    payload: MaintenanceVerifyRequest,
    db: DbSession,
    actor: MaintenanceVerifier,
    _: CsrfProtected,
) -> MaintenanceRecordResponse:
    return service.verify_record(db, actor=actor, record_id=record_id, payload=payload)


@router.post("/{record_id}/attachments", response_model=StoredFileResponse, status_code=201, tags=["maintenance", "files"])
def upload_maintenance_attachment(
    record_id: uuid.UUID,
    db: DbSession,
    actor: FileUploader,
    file: Annotated[UploadFile, File(...)],
    purpose: Annotated[str, Form()] = "maintenance_attachment",
) -> StoredFileResponse:
    record = service.get_record(db, actor=actor, record_id=record_id)
    return file_service.save_uploaded_file(
        db,
        actor=actor,
        organization_id=record.organization_id,
        upload=file,
        purpose=purpose,
        maintenance_record_id=record.id,
    )
