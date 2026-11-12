from collections.abc import Sequence
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file import StoredFile


def create_stored_file(
    db: Session,
    *,
    organization_id: uuid.UUID,
    uploaded_by: uuid.UUID,
    storage_key: str,
    original_filename: str,
    media_type: str,
    size_bytes: int,
    checksum: str,
    purpose: str = "general",
    maintenance_record_id: uuid.UUID | None = None,
) -> StoredFile:
    record = StoredFile(
        organization_id=organization_id,
        uploaded_by=uploaded_by,
        maintenance_record_id=maintenance_record_id,
        storage_key=storage_key,
        original_filename=original_filename,
        media_type=media_type,
        size_bytes=size_bytes,
        checksum=checksum,
        purpose=purpose,
    )
    db.add(record)
    db.flush()
    return record


def get_stored_file_by_id(db: Session, file_id: uuid.UUID | str) -> StoredFile | None:
    fid = file_id if isinstance(file_id, uuid.UUID) else uuid.UUID(str(file_id))
    return db.scalar(select(StoredFile).where(StoredFile.id == fid))


def list_files_by_maintenance_record(db: Session, maintenance_record_id: uuid.UUID | str) -> Sequence[StoredFile]:
    m_id = maintenance_record_id if isinstance(maintenance_record_id, uuid.UUID) else uuid.UUID(str(maintenance_record_id))
    return db.scalars(
        select(StoredFile)
        .where(StoredFile.maintenance_record_id == m_id)
        .order_by(StoredFile.created_at.desc())
    ).all()


def list_files_by_organization(
    db: Session,
    organization_id: uuid.UUID | str,
    limit: int = 50,
) -> Sequence[StoredFile]:
    oid = organization_id if isinstance(organization_id, uuid.UUID) else uuid.UUID(str(organization_id))
    return db.scalars(
        select(StoredFile)
        .where(StoredFile.organization_id == oid)
        .order_by(StoredFile.created_at.desc())
        .limit(limit)
    ).all()

