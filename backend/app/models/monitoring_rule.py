from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import GUID, UTCDateTime
from app.models.enums import INTEGRITY_CHECKS, RuleOperator, Severity

if TYPE_CHECKING:
    from app.models.equipment import EquipmentType
    from app.models.organization import Organization
    from app.models.user import User


class MonitoringRule(Base):
    __tablename__ = "monitoring_rules"
    __table_args__ = (
        CheckConstraint(INTEGRITY_CHECKS["ck_monitoring_rules_operator"], name="ck_monitoring_rules_operator"),
        CheckConstraint(INTEGRITY_CHECKS["ck_monitoring_rules_severity"], name="ck_monitoring_rules_severity"),
        Index("ix_monitoring_rules_org", "organization_id"),
        Index("ix_monitoring_rules_org_enabled", "organization_id", "is_enabled"),
        Index("ix_monitoring_rules_eq_type", "equipment_type_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    equipment_type_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("equipment_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    measurement_type: Mapped[str] = mapped_column(String(100), nullable=False)
    operator: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RuleOperator.GT.value,
    )
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=Severity.MEDIUM.value,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    organization: Mapped["Organization"] = relationship()
    equipment_type: Mapped["EquipmentType | None"] = relationship()
    creator: Mapped["User"] = relationship()

