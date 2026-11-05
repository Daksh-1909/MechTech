"""add versioned sensor reading metadata

Revision ID: d41c2f09a713
Revises: febd5d91d744
Create Date: 2026-11-05 15:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d41c2f09a713"
down_revision: str | Sequence[str] | None = "febd5d91d744"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sensor_readings",
        sa.Column("schema_version", sa.String(length=20), server_default="1.0", nullable=False),
    )
    op.add_column("sensor_readings", sa.Column("sequence_number", sa.Integer(), nullable=True))
    op.add_column("sensor_readings", sa.Column("speed_rpm", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("load_percent", sa.Float(), nullable=True))
    op.add_column("sensor_readings", sa.Column("scenario_id", sa.String(length=100), nullable=True))
    op.add_column(
        "sensor_readings", sa.Column("scenario_label", sa.String(length=50), nullable=True)
    )
    op.add_column("sensor_readings", sa.Column("simulation_seed", sa.Integer(), nullable=True))
    op.add_column(
        "sensor_readings", sa.Column("simulation_run_id", sa.String(length=100), nullable=True)
    )
    op.create_index(
        "ix_readings_equipment_sequence",
        "sensor_readings",
        ["equipment_id", "sequence_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_readings_equipment_sequence", table_name="sensor_readings")
    op.drop_column("sensor_readings", "simulation_run_id")
    op.drop_column("sensor_readings", "simulation_seed")
    op.drop_column("sensor_readings", "scenario_label")
    op.drop_column("sensor_readings", "scenario_id")
    op.drop_column("sensor_readings", "load_percent")
    op.drop_column("sensor_readings", "speed_rpm")
    op.drop_column("sensor_readings", "sequence_number")
    op.drop_column("sensor_readings", "schema_version")
