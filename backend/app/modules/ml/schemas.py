from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

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
    predicted_class: str
    probabilities_json: dict[str, Any] | None
    confidence_value: float | None
    evidence_json: dict[str, Any] | None
    prediction_timestamp: datetime
    review_status: ReviewStatus


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_name: str
    model_version: str
    model_type: ModelType
    artifact_path: str
    feature_schema_version: str
    training_dataset_description: str | None
    evaluation_metrics_json: dict[str, Any] | None
    created_at: datetime
    is_active: bool
