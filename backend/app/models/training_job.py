from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import UTCDateTime
from app.models.enums import TrainingJobStatus


class MLTrainingJob(Base):
    __tablename__ = "ml_training_jobs"
    __table_args__ = (Index("ix_ml_training_jobs_status_created_at", "status", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    submitted_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_type: Mapped[str] = mapped_column(String(30), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TrainingJobStatus.QUEUED.value,
    )
    parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    model_registry_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_registry.id", ondelete="SET NULL"),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
