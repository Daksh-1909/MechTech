"""StoredFile entity for secure local file storage with tenant isolation and checksum integrity."""

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import GUID, UTCDateTime
from app.models.enums import FilePurpose, INTEGRITY_CHECKS

if TYPE_CHECKING:
    from app.models.maintenance import MaintenanceRecord
    from app.models.organization import Organization
    from app.models.user import User


class StoredFile(Base):
    __tablename__ = "stored_files"
    __table_args__ = (
        CheckConstraint(
            INTEGRITY_CHECKS["ck_stored_files_purpose"],
            name="ck_stored_files_purpose",
        ),
        Index("ix_stored_files_org_purpose", "organization_id", "purpose"),
        Index("ix_stored_files_maintenance", "maintenance_record_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    maintenance_record_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("maintenance_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    purpose: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=FilePurpose.GENERAL.value,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    organization: Mapped["Organization"] = relationship()
    uploader: Mapped["User"] = relationship()
    maintenance_record: Mapped["MaintenanceRecord | None"] = relationship(back_populates="attachments")

