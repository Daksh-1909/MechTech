import math
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.config import settings
from app.core.time import utcnow
from app.models import SensorReading
from app.models.enums import ReadingQuality

ALLOWED_VIBRATION_UNITS = frozenset({"simulated_index", "mm_s_rms", "mm_s", "g", "arbitrary_unit"})


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class ReadingCreateRequest(BaseModel):
    equipment_id: str = Field(min_length=1, max_length=64)
    timestamp: datetime
    temperature_c: float | None = None
    vibration_value: float | None = None
    vibration_unit: str = Field(default="simulated_index", min_length=1, max_length=30)
    source: str = Field(default="simulator", min_length=1, max_length=50)
    source_event_id: str | None = Field(default=None, max_length=100)
    schema_version: str = Field(default="1.0", min_length=1, max_length=20)
    sequence_number: int | None = Field(default=None, ge=0)
    speed_rpm: float | None = Field(default=None, ge=0, le=100_000)
    load_percent: float | None = Field(default=None, ge=0, le=100)
    scenario_id: str | None = Field(default=None, max_length=100)
    scenario_label: str | None = Field(default=None, max_length=50)
    simulation_seed: int | None = None
    simulation_run_id: str | None = Field(default=None, max_length=100)
    quality_status: ReadingQuality = ReadingQuality.VALID

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        normalized = _to_utc(value)
        tolerance = timedelta(seconds=settings.reading_future_tolerance_seconds)
        if normalized > utcnow() + tolerance:
            raise ValueError("Timestamp is implausibly far in the future.")
        return normalized

    @field_validator("temperature_c")
    @classmethod
    def validate_temperature(cls, value: float | None) -> float | None:
        if value is None:
            return None
        if not math.isfinite(value):
            raise ValueError("Temperature must be a finite numeric value.")
        if not settings.temperature_min_c <= value <= settings.temperature_max_c:
            raise ValueError("Temperature is outside the configured prototype bounds.")
        return value

    @field_validator("vibration_value")
    @classmethod
    def validate_vibration(cls, value: float | None) -> float | None:
        if value is None:
            return None
        if not math.isfinite(value):
            raise ValueError("Vibration must be a finite numeric value.")
        if not settings.vibration_min <= value <= settings.vibration_max:
            raise ValueError("Vibration is outside the configured prototype bounds.")
        return value

    @field_validator("vibration_unit")
    @classmethod
    def validate_unit(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_VIBRATION_UNITS:
            raise ValueError("Unsupported vibration unit.")
        return normalized

    @field_validator("source_event_id")
    @classmethod
    def normalize_event_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_channels(self) -> "ReadingCreateRequest":
        if self.temperature_c is None and self.vibration_value is None:
            raise ValueError("At least one sensor channel is required.")
        return self


class ReadingBatchRequest(BaseModel):
    readings: list[ReadingCreateRequest] = Field(min_length=1)

    @field_validator("readings")
    @classmethod
    def validate_batch_size(
        cls,
        value: list[ReadingCreateRequest],
    ) -> list[ReadingCreateRequest]:
        if len(value) > settings.readings_batch_max:
            raise ValueError(f"A batch may contain at most {settings.readings_batch_max} readings.")
        return value


class ReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipment_id: str
    timestamp: datetime
    received_at: datetime
    temperature_c: float | None
    vibration_value: float | None
    vibration_unit: str
    source: str
    source_event_id: str | None
    schema_version: str = "1.0"
    sequence_number: int | None = None
    speed_rpm: float | None = None
    load_percent: float | None = None
    scenario_id: str | None = None
    scenario_label: str | None = None
    simulation_seed: int | None = None
    simulation_run_id: str | None = None
    quality_status: ReadingQuality

    @classmethod
    def from_model(cls, reading: SensorReading) -> "ReadingResponse":
        return cls.model_validate(reading)


class ReadingIngestResponse(BaseModel):
    reading: ReadingResponse
    duplicate: bool


class ReadingBatchResponse(BaseModel):
    created: int
    duplicates: int
    readings: list[ReadingResponse]


class ReadingSummaryResponse(BaseModel):
    equipment_id: str
    from_timestamp: datetime | None
    to_timestamp: datetime | None
    count: int
    temperature_min: float | None
    temperature_max: float | None
    temperature_avg: float | None
    vibration_min: float | None
    vibration_max: float | None
    vibration_avg: float | None
