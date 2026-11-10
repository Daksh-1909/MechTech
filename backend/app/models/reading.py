from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import GUID, JSONType, UTCDateTime
from app.models.enums import ReadingQuality

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.organization import Organization
    from app.models.sensor import Sensor


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (
        UniqueConstraint(
            "equipment_id",
            "source",
            "source_event_id",
            name="uq_readings_equipment_source_event",
        ),
        Index("ix_readings_equipment_timestamp", "equipment_id", "timestamp"),
        Index("ix_readings_sensor_timestamp", "sensor_id", "timestamp"),
        Index("ix_readings_org_timestamp", "organization_id", "timestamp"),
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
    sensor_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("sensors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Multi-channel properties for electric motor telemetry
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    vibration_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    vibration_unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="simulated_index",
    )
    speed_rpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    source: Mapped[str] = mapped_column(String(50), nullable=False, default="simulator")
    source_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scenario_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scenario_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    simulation_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    simulation_run_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quality_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReadingQuality.VALID.value,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    organization: Mapped["Organization"] = relationship()
    equipment: Mapped["Equipment"] = relationship(back_populates="readings")
    sensor: Mapped["Sensor | None"] = relationship()

    @property
    def recorded_at(self) -> datetime:
        return self.timestamp

    @property
    def idempotency_key(self) -> str | None:
        return self.source_event_id
