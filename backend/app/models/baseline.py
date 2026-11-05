from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, String, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import UTCDateTime


class BaselineProfile(Base):
    __tablename__ = "baseline_profiles"
    __table_args__ = (
        UniqueConstraint("baseline_name", "baseline_version", name="uq_baseline_name_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    baseline_name: Mapped[str] = mapped_column(String(100), nullable=False)
    baseline_version: Mapped[str] = mapped_column(String(50), nullable=False)
    feature_schema_version: Mapped[str] = mapped_column(String(30), nullable=False)
    training_sample_count: Mapped[int] = mapped_column(nullable=False)
    training_dataset_description: Mapped[str] = mapped_column(String(500), nullable=False)
    means_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    standard_deviations_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    z_threshold: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
