from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import UTCDateTime
from app.models.enums import INTEGRITY_CHECKS, EquipmentStatus

if TYPE_CHECKING:
    from app.models.reading import SensorReading


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (
        CheckConstraint(INTEGRITY_CHECKS["ck_equipment_status"], name="ck_equipment_status"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="electric_motor")
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=EquipmentStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    components: Mapped[list["Component"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    readings: Mapped[list["SensorReading"]] = relationship(
        back_populates="equipment",
        passive_deletes=True,
    )

    @property
    def is_archived(self) -> bool:
        return self.status == EquipmentStatus.ARCHIVED.value


class Component(Base):
    __tablename__ = "components"
    __table_args__ = (
        UniqueConstraint("equipment_id", "component_key", name="uq_components_equipment_key"),
        Index("ix_components_equipment_id", "equipment_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    component_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    equipment: Mapped["Equipment"] = relationship(back_populates="components")
