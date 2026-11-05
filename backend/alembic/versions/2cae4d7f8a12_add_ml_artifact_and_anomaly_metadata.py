"""add model artifact integrity and anomaly provenance

Revision ID: 2cae4d7f8a12
Revises: 76b018d90c4e
Create Date: 2026-11-05 16:45:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "2cae4d7f8a12"
down_revision: str | Sequence[str] | None = "76b018d90c4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "model_registry", sa.Column("artifact_sha256", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "model_registry", sa.Column("training_dataset_version", sa.String(length=50), nullable=True)
    )
    op.add_column("anomaly_events", sa.Column("feature_window_id", sa.Integer(), nullable=True))
    op.add_column("anomaly_events", sa.Column("detector_name", sa.String(length=50), nullable=True))
    op.add_column("anomaly_events", sa.Column("model_version", sa.String(length=50), nullable=True))
    with op.batch_alter_table("anomaly_events", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_anomaly_events_feature_window_id_feature_windows",
            "feature_windows",
            ["feature_window_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_anomaly_events_feature_window_id",
            ["feature_window_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("anomaly_events", schema=None) as batch_op:
        batch_op.drop_index("ix_anomaly_events_feature_window_id")
        batch_op.drop_constraint(
            "fk_anomaly_events_feature_window_id_feature_windows",
            type_="foreignkey",
        )
    op.drop_column("anomaly_events", "model_version")
    op.drop_column("anomaly_events", "detector_name")
    op.drop_column("anomaly_events", "feature_window_id")
    op.drop_column("model_registry", "training_dataset_version")
    op.drop_column("model_registry", "artifact_sha256")
