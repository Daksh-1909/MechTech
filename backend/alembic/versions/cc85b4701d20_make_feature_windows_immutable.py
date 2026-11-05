"""allow immutable feature-window snapshots when late readings arrive

Revision ID: cc85b4701d20
Revises: b768e7f9c2a1
Create Date: 2026-11-05 18:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "cc85b4701d20"
down_revision: str | Sequence[str] | None = "b768e7f9c2a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("feature_windows", schema=None) as batch_op:
        batch_op.drop_constraint("uq_feature_windows_equipment_start_schema", type_="unique")
        batch_op.add_column(sa.Column("snapshot_key", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint(
            "uq_feature_windows_snapshot",
            ["equipment_id", "window_start", "feature_schema_version", "snapshot_key"],
        )


def downgrade() -> None:
    with op.batch_alter_table("feature_windows", schema=None) as batch_op:
        batch_op.drop_constraint("uq_feature_windows_snapshot", type_="unique")
        batch_op.drop_column("snapshot_key")
        batch_op.create_unique_constraint(
            "uq_feature_windows_equipment_start_schema",
            ["equipment_id", "window_start", "feature_schema_version"],
        )
