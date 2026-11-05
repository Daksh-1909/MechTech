from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.db.base import Base
from app.db.types import UTCDateTime


class FeatureWindow(Base):
    __tablename__ = "feature_windows"
    __table_args__ = (
        UniqueConstraint(
            "equipment_id",
            "window_start",
            "feature_schema_version",
            "snapshot_key",
            name="uq_feature_windows_snapshot",
        ),
        Index("ix_feature_windows_equipment_end", "equipment_id", "window_end"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    window_start: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    window_end: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    feature_schema_version: Mapped[str] = mapped_column(String(30), nullable=False)
    snapshot_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    feature_values_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    source_reading_ids_json: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    incomplete_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
