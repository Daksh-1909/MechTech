from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import GUID, JSONType, UTCDateTime
from app.models.enums import INTEGRITY_CHECKS, ModelStatus

if TYPE_CHECKING:
    from app.models.equipment import EquipmentType


class MLModel(Base):
    __tablename__ = "ml_models"
    __table_args__ = (
        UniqueConstraint("model_key", "version", name="uq_ml_models_key_version"),
        CheckConstraint(INTEGRITY_CHECKS["ck_ml_models_status"], name="ck_ml_models_status"),
        Index("ix_ml_models_key_status", "model_key", "status"),
        Index("ix_ml_models_eq_type", "equipment_type_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    model_key: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    equipment_type_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("equipment_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    artifact_path: Mapped[str] = mapped_column(String(500), nullable=False)
    feature_schema: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    dataset_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ModelStatus.DRAFT.value,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)

    equipment_type: Mapped["EquipmentType | None"] = relationship()

