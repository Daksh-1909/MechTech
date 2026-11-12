from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import GUID, JSONType, UTCDateTime
from app.models.enums import INTEGRITY_CHECKS, ReviewStatus
from app.models.ml_model import MLModel

if TYPE_CHECKING:
    from app.models.anomaly import AnomalyEvent
    from app.models.equipment import Equipment
    from app.models.organization import Organization


# Alias for backwards compatibility
ModelRegistry = MLModel


class MLPrediction(Base):
    __tablename__ = "ml_predictions"
    __table_args__ = (
        CheckConstraint(
            INTEGRITY_CHECKS["ck_predictions_review"],
            name="ck_predictions_review",
        ),
        Index("ix_ml_predictions_org_timestamp", "organization_id", "prediction_timestamp"),
        Index("ix_ml_predictions_equipment_timestamp", "equipment_id", "prediction_timestamp"),
        Index("ix_ml_predictions_model", "model_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("ml_models.id", ondelete="SET NULL"),
        nullable=True,
    )
    anomaly_event_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("anomaly_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    window_start: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    window_end: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    predicted_class: Mapped[str] = mapped_column(String(50), nullable=False)
    probabilities_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    confidence_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    feature_snapshot_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
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

    organization: Mapped["Organization"] = relationship()
    equipment: Mapped["Equipment"] = relationship()
    model: Mapped["MLModel | None"] = relationship()
    anomaly_event: Mapped["AnomalyEvent | None"] = relationship()
