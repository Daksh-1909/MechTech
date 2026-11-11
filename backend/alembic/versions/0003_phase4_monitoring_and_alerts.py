"""Phase 4: Monitoring Rules, Anomaly Events, and Alerts

Revision ID: 0003_phase4_monitoring_and_alerts
Revises: 0002_phase2_equipment_and_sensors
Create Date: 2026-11-11 17:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.types import GUID, JSONType, UTCDateTime

# revision identifiers, used by Alembic.
revision: str = "0003_phase4_monitoring_and_alerts"
down_revision: Union[str, Sequence[str], None] = "0002_phase2_equipment_and_sensors"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Monitoring Rules
    op.create_table(
        "monitoring_rules",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("equipment_type_id", GUID(), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("measurement_type", sa.String(length=100), nullable=False),
        sa.Column("operator", sa.String(length=20), server_default="gt", nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_by", GUID(), nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("updated_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["equipment_type_id"], ["equipment_types.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("operator IN ('gt', 'gte', 'lt', 'lte', 'eq', 'neq')", name="ck_monitoring_rules_operator"),
        sa.CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name="ck_monitoring_rules_severity"),
    )
    op.create_index("ix_monitoring_rules_org", "monitoring_rules", ["organization_id"])
    op.create_index("ix_monitoring_rules_org_enabled", "monitoring_rules", ["organization_id", "is_enabled"])
    op.create_index("ix_monitoring_rules_eq_type", "monitoring_rules", ["equipment_type_id"])

    # 2. Anomaly Events
    op.create_table(
        "anomaly_events",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("equipment_id", GUID(), nullable=False),
        sa.Column("sensor_id", GUID(), nullable=True),
        sa.Column("rule_id", GUID(), nullable=True),
        sa.Column("component_id", GUID(), nullable=True),
        sa.Column("detector_name", sa.String(length=50), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="low", nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("start_timestamp", UTCDateTime(), nullable=False),
        sa.Column("end_timestamp", UTCDateTime(), nullable=True),
        sa.Column("anomaly_score", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_json", JSONType(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="detected", nullable=False),
        sa.Column("review_status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["component_id"], ["components.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["monitoring_rules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name="ck_anomaly_severity"),
        sa.CheckConstraint("review_status IN ('pending', 'confirmed', 'rejected')", name="ck_anomaly_review"),
    )
    op.create_index("ix_anomaly_events_org_start", "anomaly_events", ["organization_id", "start_timestamp"])
    op.create_index("ix_anomaly_events_equipment_start", "anomaly_events", ["equipment_id", "start_timestamp"])
    op.create_index("ix_anomaly_events_rule", "anomaly_events", ["rule_id"])

    # 3. Alerts
    op.create_table(
        "alerts",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("equipment_id", GUID(), nullable=False),
        sa.Column("anomaly_event_id", GUID(), nullable=True),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="low", nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="open", nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("acknowledged_at", UTCDateTime(), nullable=True),
        sa.Column("acknowledged_by", GUID(), nullable=True),
        sa.Column("resolved_at", UTCDateTime(), nullable=True),
        sa.Column("resolved_by", GUID(), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["anomaly_event_id"], ["anomaly_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name="ck_alerts_severity"),
        sa.CheckConstraint("status IN ('open', 'acknowledged', 'resolved', 'dismissed')", name="ck_alerts_status"),
    )
    op.create_index("ix_alerts_org_status_created", "alerts", ["organization_id", "status", "created_at"])
    op.create_index("ix_alerts_equipment_status", "alerts", ["equipment_id", "status"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("anomaly_events")
    op.drop_table("monitoring_rules")

