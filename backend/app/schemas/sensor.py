"""Versioned Phase 3 sensor contract, extended from Phase 2's flat reading fields."""

import math
from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.config import settings
from app.core.time import utcnow


def _finite_number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Measurement values must be numeric.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Measurement values must be finite.")
    return number


class SensorReadingPayload(BaseModel):
    """Phase 3 contract v1.0 using the established Phase 2 reading field names."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    equipment_id: str = Field(min_length=1, max_length=64)
    timestamp: datetime
    sequence: int = Field(ge=0)
    source: str = Field(min_length=1, max_length=50)
    source_event_id: str = Field(min_length=1, max_length=100)
    temperature_c: float
    vibration_value: float
    vibration_unit: Literal["simulated_index", "mm_s_rms", "mm_s", "g", "arbitrary_unit"]
    speed_rpm: float | None = Field(default=None, ge=0, le=100_000)
    load_percent: float | None = Field(default=None, ge=0, le=100)
    scenario_id: str | None = Field(default=None, max_length=100)
    scenario_label: (
        Literal[
            "normal",
            "excessive_vibration",
            "overheating",
            "bearing_abnormality",
            "combined_abnormality",
        ]
        | None
    ) = None
    simulation_seed: int | None = None
    simulation_run_id: str | None = Field(default=None, max_length=100)

    @field_validator("temperature_c", "vibration_value", mode="before")
    @classmethod
    def validate_numeric(cls, value: object) -> float:
        return _finite_number(value)

    @field_validator("timestamp")
    @classmethod
    def require_recent_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone.")
        normalized = value.astimezone(UTC)
        tolerance = timedelta(seconds=settings.reading_future_tolerance_seconds)
        if normalized > utcnow() + tolerance:
            raise ValueError("Timestamp is implausibly far in the future.")
        return normalized

    @field_validator("equipment_id", "source", "source_event_id")
    @classmethod
    def trim_identifiers(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Identifier values cannot be blank.")
        return normalized

    @model_validator(mode="after")
    def validate_configured_bounds(self) -> "SensorReadingPayload":
        if not settings.temperature_min_c <= self.temperature_c <= settings.temperature_max_c:
            raise ValueError("Temperature is outside the configured prototype bounds.")
        if not settings.vibration_min <= self.vibration_value <= settings.vibration_max:
            raise ValueError("Vibration is outside the configured prototype bounds.")
        if self.vibration_value < 0:
            raise ValueError("Vibration magnitude cannot be negative.")
        return self


class SensorReadingBatchPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    readings: list[SensorReadingPayload] = Field(
        min_length=1,
        max_length=settings.readings_batch_max,
    )
