from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import UTCDateTime
from app.models.enums import INTEGRITY_CHECKS, MaintenanceOutcome, VerificationStatus

if TYPE_CHECKING:
    from app.models.anomaly import Alert
    from app.models.equipment import Equipment
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
        Index(
            "ix_maintenance_records_equipment_inspection",
            "equipment_id",
            "inspection_timestamp",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    related_alert_id: Mapped[int | None] = mapped_column(
        ForeignKey("alerts.id", ondelete="SET NULL"),
        nullable=True,
    )
    technician_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    inspection_timestamp: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostic_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_performed: Mapped[str | None] = mapped_column(Text, nullable=True)
    parts_replaced_json: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
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
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    equipment: Mapped["Equipment"] = relationship()
    related_alert: Mapped["Alert | None"] = relationship()
    technician: Mapped["User"] = relationship()
