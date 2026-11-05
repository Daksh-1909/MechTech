"""link predictions to feature windows and training versions

Revision ID: b768e7f9c2a1
Revises: 2cae4d7f8a12
Create Date: 2026-11-05 17:30:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.types import UTCDateTime

revision: str = "b768e7f9c2a1"
down_revision: str | Sequence[str] | None = "2cae4d7f8a12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ml_predictions", sa.Column("feature_window_id", sa.Integer(), nullable=True))
    op.add_column(
        "ml_predictions", sa.Column("window_start", UTCDateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "ml_predictions", sa.Column("window_end", UTCDateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "ml_predictions", sa.Column("training_dataset_version", sa.String(length=50), nullable=True)
    )
    with op.batch_alter_table("ml_predictions", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_ml_predictions_feature_window_feature_windows",
            "feature_windows",
            ["feature_window_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_ml_predictions_feature_window", ["feature_window_id"])


def downgrade() -> None:
    with op.batch_alter_table("ml_predictions", schema=None) as batch_op:
        batch_op.drop_index("ix_ml_predictions_feature_window")
        batch_op.drop_constraint(
            "fk_ml_predictions_feature_window_feature_windows",
            type_="foreignkey",
        )
    op.drop_column("ml_predictions", "training_dataset_version")
    op.drop_column("ml_predictions", "window_end")
    op.drop_column("ml_predictions", "window_start")
    op.drop_column("ml_predictions", "feature_window_id")
