from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import UTCDateTime
from app.models.enums import INTEGRITY_CHECKS, ModelType, ReviewStatus

if TYPE_CHECKING:
    from app.models.equipment import Equipment


class ModelRegistry(Base):
    __tablename__ = "model_registry"
    __table_args__ = (
        UniqueConstraint("model_name", "model_version", name="uq_model_registry_name_version"),
        CheckConstraint(INTEGRITY_CHECKS["ck_models_type"], name="ck_models_type"),
        Index("ix_model_registry_type_active", "model_type", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=ModelType.CLASSIFICATION.value,
    )
    artifact_path: Mapped[str] = mapped_column(String(500), nullable=False)
    feature_schema_version: Mapped[str] = mapped_column(String(50), nullable=False)
    training_dataset_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_metrics_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    artifact_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    training_dataset_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )


class MLPrediction(Base):
    __tablename__ = "ml_predictions"
    __table_args__ = (
        CheckConstraint(
            INTEGRITY_CHECKS["ck_predictions_review"],
            name="ck_predictions_review",
        ),
        Index("ix_ml_predictions_equipment_timestamp", "equipment_id", "prediction_timestamp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    anomaly_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("anomaly_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_registry_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_registry.id", ondelete="SET NULL"),
        nullable=True,
    )
    predicted_class: Mapped[str] = mapped_column(String(50), nullable=False)
    probabilities_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    confidence_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    prediction_timestamp: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=utcnow,
    )
    review_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReviewStatus.PENDING.value,
    )

    equipment: Mapped["Equipment"] = relationship()
    model_registry: Mapped["ModelRegistry | None"] = relationship()
