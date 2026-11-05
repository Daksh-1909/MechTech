"""add persisted feature windows

Revision ID: 82fb6c16e790
Revises: d41c2f09a713
Create Date: 2026-11-05 15:45:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.types import UTCDateTime

revision: str = "82fb6c16e790"
down_revision: str | Sequence[str] | None = "d41c2f09a713"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "feature_windows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("equipment_id", sa.String(length=64), nullable=False),
        sa.Column("window_start", UTCDateTime(timezone=True), nullable=False),
        sa.Column("window_end", UTCDateTime(timezone=True), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("feature_schema_version", sa.String(length=30), nullable=False),
        sa.Column("feature_values_json", sa.JSON(), nullable=False),
        sa.Column("source_reading_ids_json", sa.JSON(), nullable=False),
        sa.Column("incomplete_reason", sa.String(length=200), nullable=True),
        sa.Column("created_at", UTCDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "equipment_id",
            "window_start",
            "feature_schema_version",
            name="uq_feature_windows_equipment_start_schema",
        ),
    )
    op.create_index(
        "ix_feature_windows_equipment_end",
        "feature_windows",
        ["equipment_id", "window_end"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_feature_windows_equipment_end", table_name="feature_windows")
    op.drop_table("feature_windows")
