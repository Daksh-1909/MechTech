from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import MaintenanceOutcome, VerificationStatus


class MaintenanceCreateRequest(BaseModel):
    equipment_id: str
    related_alert_id: int | None = None
    inspection_timestamp: datetime
    symptoms: str | None = None
    diagnostic_findings: str | None = None
    work_performed: str | None = None
    parts_replaced_json: list[Any] | None = None
    outcome: MaintenanceOutcome = MaintenanceOutcome.PENDING_VERIFICATION
    verification_status: VerificationStatus = VerificationStatus.PENDING
    notes: str | None = None


class MaintenanceUpdateRequest(BaseModel):
    symptoms: str | None = None
    diagnostic_findings: str | None = None
    work_performed: str | None = None
    parts_replaced_json: list[Any] | None = None
    outcome: MaintenanceOutcome | None = None
    verification_status: VerificationStatus | None = None
    notes: str | None = None


class MaintenanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipment_id: str
    related_alert_id: int | None
    technician_id: int
    inspection_timestamp: datetime
    symptoms: str | None
    diagnostic_findings: str | None
    work_performed: str | None
    parts_replaced_json: list[Any] | None
    outcome: MaintenanceOutcome
    verification_status: VerificationStatus
    notes: str | None
    created_at: datetime
