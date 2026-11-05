from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.config import settings
from app.models.enums import ModelType, ReviewStatus


class TrainingJobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_type: ModelType
    model_name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    model_version: str = Field(
        min_length=1, max_length=50, pattern=r"^[A-Za-z0-9][A-Za-z0-9.+_-]*$"
    )
    runs: int = Field(default=6, ge=2, le=20)
    test_runs: int = Field(default=2, ge=1, le=5)
    samples_per_scenario: int = Field(default=120, ge=40, le=1000)
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
    minimum_score: float = Field(default=0.4, ge=0, le=1)
    contamination: float = Field(default=0.05, gt=0, le=0.5)


class TrainingJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    model_type: str
    model_name: str
    model_version: str
    status: str
    parameters_json: dict[str, Any]
    result_json: dict[str, Any] | None
    model_registry_id: int | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


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
