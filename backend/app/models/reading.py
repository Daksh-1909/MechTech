from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import UTCDateTime
from app.models.enums import INTEGRITY_CHECKS, ReadingQuality

if TYPE_CHECKING:
    from app.models.equipment import Equipment


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
        Index("ix_readings_equipment_sequence", "equipment_id", "sequence_number", unique=True),
        CheckConstraint(
            "temperature_c IS NOT NULL OR vibration_value IS NOT NULL",
            name="ck_readings_at_least_one_channel",
        ),
        CheckConstraint(INTEGRITY_CHECKS["ck_readings_quality"], name="ck_readings_quality"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    vibration_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    vibration_unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="simulated_index",
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="simulator")
    source_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speed_rpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    scenario_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scenario_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    simulation_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    simulation_run_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quality_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReadingQuality.VALID.value,
    )

    equipment: Mapped["Equipment"] = relationship(back_populates="readings")
