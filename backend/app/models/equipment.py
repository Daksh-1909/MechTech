from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import GUID, JSONType, UTCDateTime

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.reading import SensorReading
    from app.models.sensor import Sensor
    from app.models.user import User


class EquipmentType(Base):
    __tablename__ = "equipment_types"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    equipment: Mapped[list["Equipment"]] = relationship(back_populates="equipment_type")


class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (
        UniqueConstraint("organization_id", "asset_tag", name="uq_equipment_org_asset_tag"),
        Index("ix_equipment_org_status", "organization_id", "status"),
        Index("ix_equipment_org_type", "organization_id", "equipment_type_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    equipment_type_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("equipment_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    asset_tag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    installation_date: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="operational",
    )
    location_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    organization: Mapped["Organization"] = relationship()
    equipment_type: Mapped["EquipmentType"] = relationship(back_populates="equipment")
    creator: Mapped["User"] = relationship()

    specification: Mapped["EquipmentSpecification | None"] = relationship(
        back_populates="equipment",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    components: Mapped[list["Component"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sensors: Mapped[list["Sensor"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    assignments: Mapped[list["EquipmentAssignment"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    readings: Mapped[list["SensorReading"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def is_archived(self) -> bool:
        return self.status == "archived"


class EquipmentSpecification(Base):
    __tablename__ = "equipment_specifications"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("equipment.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    specification: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    equipment: Mapped["Equipment"] = relationship(back_populates="specification")


class Component(Base):
    __tablename__ = "components"
    __table_args__ = (
        UniqueConstraint("equipment_id", "component_key", name="uq_components_equipment_key"),
        Index("ix_components_equipment_parent", "equipment_id", "parent_component_id"),
        Index("ix_components_org", "organization_id"),
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
    parent_component_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("components.id", ondelete="SET NULL"),
        nullable=True,
    )
    component_type: Mapped[str] = mapped_column(String(100), nullable=False, default="component")
    component_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="operational")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    equipment: Mapped["Equipment"] = relationship(back_populates="components")
    parent_component: Mapped["Component | None"] = relationship(remote_side=[id])
    sensors: Mapped[list["Sensor"]] = relationship(back_populates="component")


class EquipmentAssignment(Base):
    __tablename__ = "equipment_assignments"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="primary_maintainer",
    )
    assigned_by: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    equipment: Mapped["Equipment"] = relationship(back_populates="assignments")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    assigner: Mapped["User"] = relationship(foreign_keys=[assigned_by])
