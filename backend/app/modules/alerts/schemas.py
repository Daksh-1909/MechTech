from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AlertStatus, ReviewStatus, Severity


class AnomalyEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    equipment_id: uuid.UUID
    rule_id: uuid.UUID | None = None
    sensor_id: uuid.UUID | None = None
    component_id: uuid.UUID | None = None
    detector_name: str | None = None
    model_version: str | None = None
    event_type: str
    severity: Severity
    summary: str | None = None
    start_timestamp: datetime
    end_timestamp: datetime | None = None
    anomaly_score: float | None = None
    description: str | None = None
    evidence_json: dict[str, Any] | None = None
    status: str
    review_status: str
    created_at: datetime


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    equipment_id: uuid.UUID
    anomaly_event_id: uuid.UUID | None = None
    alert_type: str
    severity: Severity
    title: str
    description: str | None = None
    status: AlertStatus
    created_at: datetime
    acknowledged_at: datetime | None = None
    acknowledged_by: uuid.UUID | None = None
    resolved_at: datetime | None = None
    resolved_by: uuid.UUID | None = None
    resolution_note: str | None = None
    anomaly_event: AnomalyEventResponse | None = None


class AlertStatusUpdateRequest(BaseModel):
    status: AlertStatus
    note: str | None = Field(default=None, max_length=1000)


class AlertActionRequest(BaseModel):
    note: str | None = Field(default=None, max_length=1000)
