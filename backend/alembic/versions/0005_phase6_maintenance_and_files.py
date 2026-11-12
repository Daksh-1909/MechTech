"""Phase 6: Maintenance Records, File Storage, and Verification

Revision ID: 0005_phase6_maintenance_and_files
Revises: 0004_phase5_hybrid_diagnostics
Create Date: 2026-11-12 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.types import GUID, JSONType, UTCDateTime

# revision identifiers, used by Alembic.
revision: str = "0005_phase6_maintenance_and_files"
down_revision: Union[str, Sequence[str], None] = "0004_phase5_hybrid_diagnostics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Maintenance Records
    # Drop existing table if present from any early draft to guarantee clean GUID-based schema
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "stored_files" in tables:
        op.drop_table("stored_files")
    if "maintenance_records" in tables:
        op.drop_table("maintenance_records")

    op.create_table(
        "maintenance_records",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("equipment_id", GUID(), nullable=False),
        sa.Column("diagnosis_id", GUID(), nullable=True),
        sa.Column("related_alert_id", GUID(), nullable=True),
        sa.Column("created_by", GUID(), nullable=False),
        sa.Column("assigned_to", GUID(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("maintenance_type", sa.String(length=30), server_default="corrective", nullable=False),
        sa.Column("status", sa.String(length=30), server_default="scheduled", nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("scheduled_at", UTCDateTime(), nullable=True),
        sa.Column("started_at", UTCDateTime(), nullable=True),
        sa.Column("completed_at", UTCDateTime(), nullable=True),
        sa.Column("inspection_timestamp", UTCDateTime(), nullable=True),
        sa.Column("symptoms", sa.Text(), nullable=True),
        sa.Column("diagnostic_findings", sa.Text(), nullable=True),
        sa.Column("work_performed", sa.Text(), nullable=True),
        sa.Column("parts_replaced_json", JSONType(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("outcome", sa.String(length=30), server_default="pending_verification", nullable=False),
        sa.Column("verification_status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("verified_by", GUID(), nullable=True),
        sa.Column("verified_at", UTCDateTime(), nullable=True),
        sa.Column("verification_note", sa.Text(), nullable=True),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("updated_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["diagnosis_id"], ["diagnoses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["related_alert_id"], ["alerts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "outcome IN ('resolved', 'not_resolved', 'inconclusive', 'pending_verification')",
            name="ck_maintenance_outcome",
        ),
        sa.CheckConstraint(
            "verification_status IN ('pending', 'verified', 'rejected')",
            name="ck_maintenance_verification",
        ),
        sa.CheckConstraint(
            "maintenance_type IN ('corrective', 'preventive', 'condition_based', 'emergency')",
            name="ck_maintenance_type",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')",
            name="ck_maintenance_status",
        ),
        sa.CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name="ck_maintenance_priority",
        ),
    )
    op.create_index("ix_maintenance_records_org_status", "maintenance_records", ["organization_id", "status"])
    op.create_index("ix_maintenance_records_equipment", "maintenance_records", ["equipment_id", "created_at"])
    op.create_index("ix_maintenance_records_alert", "maintenance_records", ["related_alert_id"])
    op.create_index("ix_maintenance_records_diagnosis", "maintenance_records", ["diagnosis_id"])

    # 2. Stored Files
    op.create_table(
        "stored_files",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("uploaded_by", GUID(), nullable=False),
        sa.Column("maintenance_record_id", GUID(), nullable=True),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=50), server_default="general", nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["maintenance_record_id"], ["maintenance_records.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key", name="uq_stored_files_storage_key"),
        sa.CheckConstraint(
            "purpose IN ('maintenance_attachment', 'vibration_report', 'inspection_photo', 'manual', 'general')",
            name="ck_stored_files_purpose",
        ),
    )
    op.create_index("ix_stored_files_org_purpose", "stored_files", ["organization_id", "purpose"])
    op.create_index("ix_stored_files_maintenance", "stored_files", ["maintenance_record_id"])


def downgrade() -> None:
    op.drop_table("stored_files")
    op.drop_table("maintenance_records")

