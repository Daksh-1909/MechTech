from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AlertStatus, Severity


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipment_id: str
    anomaly_event_id: int | None
    alert_type: str
    severity: Severity
    title: str
    description: str | None
    status: AlertStatus
    created_at: datetime
    acknowledged_by: int | None
    resolved_at: datetime | None


class AlertStatusUpdateRequest(BaseModel):
    status: AlertStatus
