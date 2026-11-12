import hashlib
from pathlib import Path
from typing import BinaryIO
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.models.file import StoredFile
from app.models.user import User
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.files import repository
from app.modules.files.schemas import StoredFileResponse

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit


def _is_platform_admin(user: User) -> bool:
    return any(
        a.role and a.role.key in {"platform_admin", "admin"}
        for a in getattr(user, "assigned_roles", [])
    )


def uploads_root() -> Path:
    target = (settings.data_root / "uploads").resolve()
    target.mkdir(parents=True, exist_ok=True)
    return target


def resolve_file_path(storage_key: str) -> Path:
    root = uploads_root()
    path = (root / storage_key).resolve()
    if not path.is_relative_to(root):
        raise AppError("Invalid file storage key: path traversal detected.", code="FORBIDDEN", status_code=403)
    return path


def save_uploaded_file(
    db: Session,
    *,
    actor: User,
    organization_id: uuid.UUID | str,
    upload: UploadFile,
    purpose: str = "general",
    maintenance_record_id: uuid.UUID | str | None = None,
) -> StoredFileResponse:
    oid = organization_id if isinstance(organization_id, uuid.UUID) else uuid.UUID(str(organization_id))

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == oid for m in memberships):
            raise AppError("Cannot upload files to an organization you do not belong to.", code="FORBIDDEN", status_code=403)
        if not has_permission(actor, Permission.FILES_UPLOAD, organization_id=oid):
            raise AppError("Permission denied to upload files.", code="FORBIDDEN", status_code=403)

    m_id = None
    if maintenance_record_id is not None:
        m_id = maintenance_record_id if isinstance(maintenance_record_id, uuid.UUID) else uuid.UUID(str(maintenance_record_id))

    # Sanitize extension
    orig_name = Path(upload.filename or "uploaded_file.bin").name
    ext = Path(orig_name).suffix[:10].lower()
    safe_file_uuid = uuid.uuid4()
    rel_key = f"{oid}/{safe_file_uuid}{ext}"

    dest_path = resolve_file_path(rel_key)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    hasher = hashlib.sha256()
    total_bytes = 0

    try:
        with dest_path.open("wb") as out_file:
            while chunk := upload.file.read(64 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE_BYTES:
                    raise AppError(
                        f"File size exceeds maximum permitted limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
                        code="FILE_TOO_LARGE",
                        status_code=413,
                    )
                hasher.update(chunk)
                out_file.write(chunk)
    except Exception:
        if dest_path.exists():
            dest_path.unlink()
        raise

    stored = repository.create_stored_file(
        db,
        organization_id=oid,
        uploaded_by=actor.id,
        storage_key=rel_key,
        original_filename=orig_name,
        media_type=upload.content_type or "application/octet-stream",
        size_bytes=total_bytes,
        checksum=hasher.hexdigest(),
        purpose=purpose,
        maintenance_record_id=m_id,
    )

    audit_service.record_event(
        db,
        action=AuditAction.FILE_UPLOADED,
        resource_type="stored_file",
        resource_id=stored.id,
        actor_user_id=actor.id,
        organization_id=oid,
        metadata={"filename": orig_name, "size_bytes": total_bytes, "purpose": purpose},
    )

    db.commit()
    db.refresh(stored)
    return StoredFileResponse.model_validate(stored)


def get_file_metadata(
    db: Session,
    *,
    actor: User,
    file_id: uuid.UUID | str,
) -> StoredFileResponse:
    stored = repository.get_stored_file_by_id(db, file_id)
    if not stored:
        raise AppError("Stored file not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == stored.organization_id for m in memberships):
            raise AppError("Access denied to this file.", code="FORBIDDEN", status_code=403)
        if not has_permission(actor, Permission.FILES_DOWNLOAD, organization_id=stored.organization_id):
            raise AppError("Permission denied to view this file.", code="FORBIDDEN", status_code=403)

    return StoredFileResponse.model_validate(stored)


def get_file_for_download(
    db: Session,
    *,
    actor: User,
    file_id: uuid.UUID | str,
) -> tuple[StoredFile, Path]:
    stored = repository.get_stored_file_by_id(db, file_id)
    if not stored:
        raise AppError("Stored file not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == stored.organization_id for m in memberships):
            raise AppError("Access denied to this file.", code="FORBIDDEN", status_code=403)
        if not has_permission(actor, Permission.FILES_DOWNLOAD, organization_id=stored.organization_id):
            raise AppError("Permission denied to download this file.", code="FORBIDDEN", status_code=403)

    disk_path = resolve_file_path(stored.storage_key)
    if not disk_path.exists():
        raise AppError("File content not found on local storage.", code="NOT_FOUND", status_code=404)

    audit_service.record_event(
        db,
        action=AuditAction.FILE_DOWNLOADED,
        resource_type="stored_file",
        resource_id=stored.id,
        actor_user_id=actor.id,
        organization_id=stored.organization_id,
        metadata={"filename": stored.original_filename},
    )
    db.commit()

    return stored, disk_path

