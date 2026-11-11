from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import (
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
from app.db.types import GUID, JSONType, UTCDateTime
from app.models.enums import INTEGRITY_CHECKS, AlertStatus, ReviewStatus, Severity

if TYPE_CHECKING:
    from app.models.equipment import Component, Equipment
    from app.models.monitoring_rule import MonitoringRule
    from app.models.organization import Organization
    from app.models.sensor import Sensor
    from app.models.user import User


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"
    __table_args__ = (
        CheckConstraint(INTEGRITY_CHECKS["ck_anomaly_severity"], name="ck_anomaly_severity"),
        CheckConstraint(INTEGRITY_CHECKS["ck_anomaly_review"], name="ck_anomaly_review"),
        Index("ix_anomaly_events_org_start", "organization_id", "start_timestamp"),
        Index("ix_anomaly_events_equipment_start", "equipment_id", "start_timestamp"),
        Index("ix_anomaly_events_rule", "rule_id"),
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
    sensor_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("sensors.id", ondelete="SET NULL"),
        nullable=True,
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("monitoring_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    component_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("components.id", ondelete="SET NULL"),
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
    summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_timestamp: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    end_timestamp: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    status: Mapped[str] = mapped_column(String(30), server_default="detected", nullable=False)
    review_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReviewStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    organization: Mapped["Organization"] = relationship()
    equipment: Mapped["Equipment"] = relationship()
    sensor: Mapped["Sensor | None"] = relationship()
    rule: Mapped["MonitoringRule | None"] = relationship()
    component: Mapped["Component | None"] = relationship()
    alerts: Mapped[list["Alert"]] = relationship(back_populates="anomaly_event")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint(INTEGRITY_CHECKS["ck_alerts_severity"], name="ck_alerts_severity"),
        CheckConstraint(INTEGRITY_CHECKS["ck_alerts_status"], name="ck_alerts_status"),
        Index("ix_alerts_org_status_created", "organization_id", "status", "created_at"),
        Index("ix_alerts_equipment_status", "equipment_id", "status"),
        Index("ix_alerts_created_at", "created_at"),
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
    anomaly_event_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
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
    acknowledged_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship()
    equipment: Mapped["Equipment"] = relationship()
    anomaly_event: Mapped["AnomalyEvent | None"] = relationship(back_populates="alerts")
    acknowledger: Mapped["User | None"] = relationship(foreign_keys=[acknowledged_by])
    resolver: Mapped["User | None"] = relationship(foreign_keys=[resolved_by])
