from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import UTCDateTime
from app.models.enums import INTEGRITY_CHECKS, AlertStatus, ReviewStatus, Severity

if TYPE_CHECKING:
    from app.models.equipment import Equipment


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"
    __table_args__ = (
        CheckConstraint(INTEGRITY_CHECKS["ck_anomaly_severity"], name="ck_anomaly_severity"),
        CheckConstraint(INTEGRITY_CHECKS["ck_anomaly_review"], name="ck_anomaly_review"),
        Index("ix_anomaly_events_equipment_start", "equipment_id", "start_timestamp"),
        Index("ix_anomaly_events_feature_window_id", "feature_window_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    component_id: Mapped[int | None] = mapped_column(
        ForeignKey("components.id", ondelete="SET NULL"),
        nullable=True,
    )
    feature_window_id: Mapped[int | None] = mapped_column(
        ForeignKey("feature_windows.id", ondelete="SET NULL"),
        nullable=True,
    )
    detector_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=Severity.LOW.value,
    )
    start_timestamp: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    end_timestamp: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReviewStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    equipment: Mapped["Equipment"] = relationship()
    alerts: Mapped[list["Alert"]] = relationship(back_populates="anomaly_event")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint(INTEGRITY_CHECKS["ck_alerts_severity"], name="ck_alerts_severity"),
        CheckConstraint(INTEGRITY_CHECKS["ck_alerts_status"], name="ck_alerts_status"),
        Index("ix_alerts_equipment_status", "equipment_id", "status"),
        Index("ix_alerts_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    anomaly_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("anomaly_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=Severity.LOW.value,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AlertStatus.OPEN.value,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    acknowledged_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    equipment: Mapped["Equipment"] = relationship()
    anomaly_event: Mapped["AnomalyEvent | None"] = relationship(back_populates="alerts")
