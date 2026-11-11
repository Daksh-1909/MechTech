from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EquipmentStatus, RuleOperator, Severity


class ReadingSnapshot(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    timestamp: datetime
    received_at: datetime
    temperature_c: float | None = None
    vibration_value: float | None = None
    vibration_unit: str | None = None
    speed_rpm: float | None = None
    load_percent: float | None = None
    quality_status: str


class EquipmentStatusResponse(BaseModel):
    equipment_id: uuid.UUID
    name: str
    status: str
    latest_reading: ReadingSnapshot | None = None
    seconds_since_latest: float | None = None
    is_stale: bool
    stale_threshold_seconds: int
    open_alert_count: int


class MonitoringRuleCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    organization_id: uuid.UUID | None = None
    equipment_type_id: uuid.UUID | None = None
    measurement_type: str = Field(min_length=1, max_length=100)
    operator: RuleOperator = RuleOperator.GT
    threshold: float
    unit: str = Field(min_length=1, max_length=50)
    duration_seconds: int = Field(default=0, ge=0, le=86400)
    severity: Severity = Severity.MEDIUM
    is_enabled: bool = True


class MonitoringRuleUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    operator: RuleOperator | None = None
    threshold: float | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=50)
    duration_seconds: int | None = Field(default=None, ge=0, le=86400)
    severity: Severity | None = None
    is_enabled: bool | None = None


class MonitoringRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    equipment_type_id: uuid.UUID | None = None
    name: str
    measurement_type: str
    operator: str
    threshold: float
    unit: str
    duration_seconds: int
    severity: str
    is_enabled: bool
    version: int
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
