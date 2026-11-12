from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    MaintenanceOutcome,
    MaintenancePriority,
    MaintenanceStatus,
    MaintenanceType,
    VerificationStatus,
)
from app.modules.files.schemas import StoredFileResponse


class MaintenanceRecordCreate(BaseModel):
    equipment_id: uuid.UUID
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    maintenance_type: str = Field(default=MaintenanceType.CORRECTIVE.value)
    priority: str = Field(default=MaintenancePriority.MEDIUM.value)
    status: str = Field(default=MaintenanceStatus.SCHEDULED.value)
    diagnosis_id: uuid.UUID | None = None
    related_alert_id: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None
    scheduled_at: datetime | None = None
    inspection_timestamp: datetime | None = None
    symptoms: str | None = None
    diagnostic_findings: str | None = None
    work_performed: str | None = None
    parts_replaced_json: list[Any] | None = None
    notes: str | None = None


class MaintenanceRecordUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    maintenance_type: str | None = None
    priority: str | None = None
    status: str | None = None
    assigned_to: uuid.UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    inspection_timestamp: datetime | None = None
    symptoms: str | None = None
    diagnostic_findings: str | None = None
    work_performed: str | None = None
    parts_replaced_json: list[Any] | None = None
    outcome: str | None = None
    notes: str | None = None


class MaintenanceVerifyRequest(BaseModel):
    verification_status: str = Field(pattern=r"^(verified|rejected)$")
    verification_note: str | None = Field(default=None, max_length=1000)


class MaintenanceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    equipment_id: uuid.UUID
    diagnosis_id: uuid.UUID | None = None
    related_alert_id: uuid.UUID | None = None
    created_by: uuid.UUID
    assigned_to: uuid.UUID | None = None
    title: str
    description: str | None = None
    maintenance_type: str
    status: str
    priority: str
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    inspection_timestamp: datetime | None = None
    symptoms: str | None = None
    diagnostic_findings: str | None = None
    work_performed: str | None = None
    parts_replaced_json: list[Any] | None = None
    outcome: str
    verification_status: str
    verified_by: uuid.UUID | None = None
    verified_at: datetime | None = None
    verification_note: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    equipment_name: str | None = None
    equipment_asset_tag: str | None = None
    attachments: list[StoredFileResponse] = Field(default_factory=list)
