"""Phase 2: Equipment Types, Equipment, Specifications, Components, Assignments, Sensors, and Readings

Revision ID: 0002_phase2_equipment_and_sensors
Revises: 0001_phase0_phase1
Create Date: 2026-11-10 19:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.types import GUID, JSONType, UTCDateTime

# revision identifiers, used by Alembic.
revision: str = "0002_phase2_equipment_and_sensors"
down_revision: Union[str, Sequence[str], None] = "0001_phase0_phase1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Equipment Types
    op.create_table(
        "equipment_types",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("schema_version", sa.String(length=20), server_default="1.0", nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equipment_types_key", "equipment_types", ["key"], unique=True)

    # 2. Equipment
    op.create_table(
        "equipment",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("equipment_type_id", GUID(), nullable=False),
        sa.Column("asset_tag", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("manufacturer", sa.String(length=200), nullable=True),
        sa.Column("model_number", sa.String(length=200), nullable=True),
        sa.Column("serial_number", sa.String(length=200), nullable=True),
        sa.Column("installation_date", UTCDateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="operational", nullable=False),
        sa.Column("location_label", sa.String(length=200), nullable=True),
        sa.Column("created_by", GUID(), nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("updated_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["equipment_type_id"], ["equipment_types.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "asset_tag", name="uq_equipment_org_asset_tag"),
    )
    op.create_index("ix_equipment_org_status", "equipment", ["organization_id", "status"])
    op.create_index("ix_equipment_org_type", "equipment", ["organization_id", "equipment_type_id"])

    # 3. Equipment Specifications
    op.create_table(
        "equipment_specifications",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("equipment_id", GUID(), nullable=False),
        sa.Column("schema_version", sa.String(length=20), server_default="1.0", nullable=False),
        sa.Column("specification", JSONType(), nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("updated_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("equipment_id", name="uq_equipment_specifications_equipment"),
    )

    # 4. Components
    op.create_table(
        "components",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("equipment_id", GUID(), nullable=False),
        sa.Column("parent_component_id", GUID(), nullable=True),
        sa.Column("component_type", sa.String(length=100), server_default="component", nullable=False),
        sa.Column("component_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("manufacturer", sa.String(length=200), nullable=True),
        sa.Column("model_number", sa.String(length=200), nullable=True),
        sa.Column("serial_number", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="operational", nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("updated_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_component_id"], ["components.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("equipment_id", "component_key", name="uq_components_equipment_key"),
    )
    op.create_index("ix_components_equipment_parent", "components", ["equipment_id", "parent_component_id"])
    op.create_index("ix_components_org", "components", ["organization_id"])

    # 5. Equipment Assignments
    op.create_table(
        "equipment_assignments",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("equipment_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("assignment_type", sa.String(length=50), server_default="primary_maintainer", nullable=False),
        sa.Column("assigned_by", GUID(), nullable=False),
        sa.Column("assigned_at", UTCDateTime(), nullable=False),
        sa.Column("ended_at", UTCDateTime(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equipment_assignments_equipment", "equipment_assignments", ["equipment_id"])
    op.create_index("ix_equipment_assignments_user", "equipment_assignments", ["user_id"])

    # 6. Sensors
    op.create_table(
        "sensors",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("equipment_id", GUID(), nullable=False),
        sa.Column("component_id", GUID(), nullable=True),
        sa.Column("sensor_key", sa.String(length=100), nullable=False),
        sa.Column("measurement_type", sa.String(length=100), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("configuration", JSONType(), nullable=True),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("updated_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["component_id"], ["components.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("equipment_id", "sensor_key", name="uq_sensors_equipment_key"),
    )
    op.create_index("ix_sensors_org_equipment", "sensors", ["organization_id", "equipment_id"])

    # 7. Sensor Readings
    op.create_table(
        "sensor_readings",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("equipment_id", GUID(), nullable=False),
        sa.Column("sensor_id", GUID(), nullable=True),
        sa.Column("timestamp", UTCDateTime(), nullable=False),
        sa.Column("received_at", UTCDateTime(), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("vibration_value", sa.Float(), nullable=True),
        sa.Column("vibration_unit", sa.String(length=30), server_default="simulated_index", nullable=False),
        sa.Column("speed_rpm", sa.Float(), nullable=True),
        sa.Column("load_percent", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=50), server_default="simulator", nullable=False),
        sa.Column("source_event_id", sa.String(length=100), nullable=True),
        sa.Column("schema_version", sa.String(length=20), server_default="1.0", nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=True),
        sa.Column("scenario_id", sa.String(length=100), nullable=True),
        sa.Column("scenario_label", sa.String(length=50), nullable=True),
        sa.Column("simulation_seed", sa.Integer(), nullable=True),
        sa.Column("simulation_run_id", sa.String(length=100), nullable=True),
        sa.Column("quality_status", sa.String(length=20), server_default="valid", nullable=False),
        sa.Column("metadata_json", JSONType(), nullable=True),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("equipment_id", "source", "source_event_id", name="uq_readings_equipment_source_event"),
    )
    op.create_index("ix_readings_equipment_timestamp", "sensor_readings", ["equipment_id", "timestamp"])
    op.create_index("ix_readings_sensor_timestamp", "sensor_readings", ["sensor_id", "timestamp"])
    op.create_index("ix_readings_org_timestamp", "sensor_readings", ["organization_id", "timestamp"])


def downgrade() -> None:
    op.drop_table("sensor_readings")
    op.drop_table("sensors")
    op.drop_table("equipment_assignments")
    op.drop_table("components")
    op.drop_table("equipment_specifications")
    op.drop_table("equipment")
    op.drop_table("equipment_types")

