"""add bounded local ML training jobs

Revision ID: 57ab0906b21f
Revises: cc85b4701d20
Create Date: 2026-11-05 18:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "57ab0906b21f"
down_revision: str | Sequence[str] | None = "cc85b4701d20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ml_training_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("submitted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("model_type", sa.String(length=30), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("parameters_json", sa.JSON(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("model_registry_id", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["model_registry_id"], ["model_registry.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ml_training_jobs_status_created_at", "ml_training_jobs", ["status", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_ml_training_jobs_status_created_at", table_name="ml_training_jobs")
    op.drop_table("ml_training_jobs")
