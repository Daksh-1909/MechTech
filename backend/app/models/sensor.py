from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import GUID, JSONType, UTCDateTime

if TYPE_CHECKING:
    from app.models.equipment import Component, Equipment
    from app.models.organization import Organization


class Sensor(Base):
    __tablename__ = "sensors"
    __table_args__ = (
        UniqueConstraint("equipment_id", "sensor_key", name="uq_sensors_equipment_key"),
        Index("ix_sensors_org_equipment", "organization_id", "equipment_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    component_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("components.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sensor_key: Mapped[str] = mapped_column(String(100), nullable=False)
    measurement_type: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    configuration: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    organization: Mapped["Organization"] = relationship()
    equipment: Mapped["Equipment"] = relationship(back_populates="sensors")
    component: Mapped["Component | None"] = relationship(back_populates="sensors")

