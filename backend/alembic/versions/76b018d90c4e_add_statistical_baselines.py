"""add versioned statistical baseline profiles

Revision ID: 76b018d90c4e
Revises: 82fb6c16e790
Create Date: 2026-11-05 16:15:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.types import UTCDateTime

revision: str = "76b018d90c4e"
down_revision: str | Sequence[str] | None = "82fb6c16e790"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "baseline_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("baseline_name", sa.String(length=100), nullable=False),
        sa.Column("baseline_version", sa.String(length=50), nullable=False),
        sa.Column("feature_schema_version", sa.String(length=30), nullable=False),
        sa.Column("training_sample_count", sa.Integer(), nullable=False),
        sa.Column("training_dataset_description", sa.String(length=500), nullable=False),
        sa.Column("means_json", sa.JSON(), nullable=False),
        sa.Column("standard_deviations_json", sa.JSON(), nullable=False),
        sa.Column("z_threshold", sa.Float(), nullable=False),
        sa.Column("created_at", UTCDateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("baseline_name", "baseline_version", name="uq_baseline_name_version"),
    )


def downgrade() -> None:
    op.drop_table("baseline_profiles")
