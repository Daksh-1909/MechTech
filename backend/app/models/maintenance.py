"""MaintenanceRecord entity representing work orders, repairs, and inspections."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import GUID, JSONType, UTCDateTime
from app.models.enums import (
    INTEGRITY_CHECKS,
    MaintenanceOutcome,
    MaintenancePriority,
    MaintenanceStatus,
    MaintenanceType,
    VerificationStatus,
)

if TYPE_CHECKING:
    from app.models.anomaly import Alert
    from app.models.diagnosis import Diagnosis
    from app.models.equipment import Equipment
    from app.models.file import StoredFile
    from app.models.organization import Organization
    from app.models.user import User


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    __table_args__ = (
        CheckConstraint(
            INTEGRITY_CHECKS["ck_maintenance_outcome"],
            name="ck_maintenance_outcome",
        ),
        CheckConstraint(
            INTEGRITY_CHECKS["ck_maintenance_verification"],
            name="ck_maintenance_verification",
        ),
        CheckConstraint(
            INTEGRITY_CHECKS["ck_maintenance_type"],
            name="ck_maintenance_type",
        ),
        CheckConstraint(
            INTEGRITY_CHECKS["ck_maintenance_status"],
            name="ck_maintenance_status",
        ),
        CheckConstraint(
            INTEGRITY_CHECKS["ck_maintenance_priority"],
            name="ck_maintenance_priority",
        ),
        Index("ix_maintenance_records_org_status", "organization_id", "status"),
        Index("ix_maintenance_records_equipment", "equipment_id", "created_at"),
        Index("ix_maintenance_records_alert", "related_alert_id"),
        Index("ix_maintenance_records_diagnosis", "diagnosis_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    diagnosis_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("diagnoses.id", ondelete="SET NULL"),
        nullable=True,
    )
    related_alert_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("alerts.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Core attributes
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    maintenance_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=MaintenanceType.CORRECTIVE.value,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=MaintenanceStatus.SCHEDULED.value,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MaintenancePriority.MEDIUM.value,
    )

    # Schedule & completion times
    scheduled_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    inspection_timestamp: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    # Findings & actions
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostic_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_performed: Mapped[str | None] = mapped_column(Text, nullable=True)
    parts_replaced_json: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Outcome & verification
    outcome: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=MaintenanceOutcome.PENDING_VERIFICATION.value,
    )
    verification_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=VerificationStatus.PENDING.value,
    )
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow)

    # Relationships
    organization: Mapped["Organization"] = relationship()
    equipment: Mapped["Equipment"] = relationship()
    diagnosis: Mapped["Diagnosis | None"] = relationship()
    related_alert: Mapped["Alert | None"] = relationship()
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assigned_to])
    verifier: Mapped["User | None"] = relationship(foreign_keys=[verified_by])
    attachments: Mapped[list["StoredFile"]] = relationship(
        back_populates="maintenance_record",
        cascade="all, delete-orphan",
    )
