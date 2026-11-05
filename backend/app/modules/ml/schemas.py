from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.config import settings
from app.models.enums import ModelType, ReviewStatus


class AnalysisRequest(BaseModel):
    window_size: int = Field(
        default=settings.feature_window_size,
        ge=2,
        le=settings.analysis_window_max,
    )


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipment_id: str
    anomaly_event_id: int | None
    model_registry_id: int | None
    feature_window_id: int | None
    window_start: datetime | None
    window_end: datetime | None
    training_dataset_version: str | None
    predicted_class: str
    probabilities_json: dict[str, Any] | None
    confidence_value: float | None
    evidence_json: dict[str, Any] | None
    prediction_timestamp: datetime
    review_status: ReviewStatus

    @computed_field
    @property
    def feature_schema_version(self) -> str | None:
        return (self.evidence_json or {}).get("feature_schema_version")

    @computed_field
    @property
    def anomaly_result(self) -> dict[str, Any] | None:
        value = (self.evidence_json or {}).get("anomaly_result")
        return value if isinstance(value, dict) else None


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_name: str
    model_version: str
    model_type: ModelType
    feature_schema_version: str
    training_dataset_description: str | None
    evaluation_metrics_json: dict[str, Any] | None
    created_at: datetime
    is_active: bool


class AnomalyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipment_id: str
    feature_window_id: int | None
    detector_name: str | None
    model_version: str | None
    event_type: str
    severity: str
    start_timestamp: datetime
    end_timestamp: datetime | None
    anomaly_score: float | None
    description: str | None
    evidence_json: dict[str, Any] | None
    review_status: str
    created_at: datetime
