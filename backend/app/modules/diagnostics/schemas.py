from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DiagnosisStatus, EvidenceType, ReviewStatus, Severity


class DiagnosisEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evidence_type: str
    source_reference: str | None = None
    weight: float
    details_json: dict[str, Any]
    created_at: datetime


class DiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    equipment_id: uuid.UUID
    primary_fault_id: uuid.UUID | None = None
    primary_fault_key: str | None = None
    primary_fault_name: str | None = None
    status: str
    severity: str
    confidence_score: float
    summary: str
    diagnostic_policy_version: str
    generated_at: datetime
    reviewed_by: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    review_status: str
    evidence_items: list[DiagnosisEvidenceResponse] = Field(default_factory=list)


class DiagnosisGenerateRequest(BaseModel):
    equipment_id: uuid.UUID
    window_size: int = Field(default=12, ge=2, le=200)


class DiagnosisReviewRequest(BaseModel):
    review_status: str = Field(pattern=r"^(confirmed_by_reviewer|dismissed|rejected)$")
    review_note: str | None = Field(default=None, max_length=1000)

