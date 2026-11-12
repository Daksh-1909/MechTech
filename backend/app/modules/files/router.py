from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import DbSession
from app.modules.auth.dependencies import CurrentUser
from app.modules.files import service
from app.modules.files.schemas import StoredFileResponse

router = APIRouter()


@router.post("", response_model=StoredFileResponse, status_code=201, tags=["files"])
def upload_file(
    db: DbSession,
    user: CurrentUser,
    file: Annotated[UploadFile, File(...)],
    organization_id: Annotated[uuid.UUID, Form(...)],
    purpose: Annotated[str, Form()] = "general",
    maintenance_record_id: Annotated[uuid.UUID | None, Form()] = None,
) -> StoredFileResponse:
    return service.save_uploaded_file(
        db,
        actor=user,
        organization_id=organization_id,
        upload=file,
        purpose=purpose,
        maintenance_record_id=maintenance_record_id,
    )


@router.get("/{file_id}", response_model=StoredFileResponse, tags=["files"])
def get_file_metadata(
    file_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> StoredFileResponse:
    return service.get_file_metadata(db, actor=user, file_id=file_id)


@router.get("/{file_id}/download", tags=["files"])
def download_file(
    file_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> FileResponse:
    stored, path = service.get_file_for_download(db, actor=user, file_id=file_id)
    return FileResponse(
        path=path,
        media_type=stored.media_type,
        filename=stored.original_filename,
    )

