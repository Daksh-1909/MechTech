from datetime import datetime

from pydantic import BaseModel

from app.models.enums import EquipmentStatus, Severity


class ReadingSnapshot(BaseModel):
    id: int
    timestamp: datetime
    received_at: datetime
    temperature_c: float | None
    vibration_value: float | None
    vibration_unit: str | None = None
    quality_status: str


class EquipmentStatusResponse(BaseModel):
    equipment_id: str
    name: str
    status: EquipmentStatus
    latest_reading: ReadingSnapshot | None
    seconds_since_latest: float | None
    is_stale: bool
    stale_threshold_seconds: int
    open_alert_count: int


class AnomalyEventResponse(BaseModel):
    id: int
    equipment_id: str
    component_id: int | None
    event_type: str
    severity: Severity
    start_timestamp: datetime
    end_timestamp: datetime | None
    anomaly_score: float | None
    description: str | None
    review_status: str
