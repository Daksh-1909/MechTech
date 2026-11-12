"""Phase 5: Hybrid Diagnostics (Faults, ML Models, Predictions, Knowledge Graph, Diagnoses, Evidence)

Revision ID: 0004_phase5_hybrid_diagnostics
Revises: 0003_phase4_monitoring_and_alerts
Create Date: 2026-11-12 18:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.types import GUID, JSONType, UTCDateTime

# revision identifiers, used by Alembic.
revision: str = "0004_phase5_hybrid_diagnostics"
down_revision: Union[str, Sequence[str], None] = "0003_phase4_monitoring_and_alerts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Faults
    op.create_table(
        "faults",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("equipment_type_id", GUID(), nullable=True),
        sa.Column("default_severity", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["equipment_type_id"], ["equipment_types.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_faults_key"),
    )
    op.create_index("ix_faults_key", "faults", ["key"], unique=True)
    op.create_index("ix_faults_eq_type", "faults", ["equipment_type_id"])

    # 2. ML Models
    op.create_table(
        "ml_models",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("model_key", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("equipment_type_id", GUID(), nullable=True),
        sa.Column("artifact_path", sa.String(length=500), nullable=False),
        sa.Column("feature_schema", JSONType(), nullable=False),
        sa.Column("dataset_version", sa.String(length=50), nullable=True),
        sa.Column("metrics", JSONType(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["equipment_type_id"], ["equipment_types.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_key", "version", name="uq_ml_models_key_version"),
        sa.CheckConstraint("status IN ('draft', 'validated', 'active', 'retired')", name="ck_ml_models_status"),
    )
    op.create_index("ix_ml_models_key_status", "ml_models", ["model_key", "status"])
    op.create_index("ix_ml_models_eq_type", "ml_models", ["equipment_type_id"])

    # 3. ML Predictions
    op.create_table(
        "ml_predictions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("equipment_id", GUID(), nullable=False),
        sa.Column("model_id", GUID(), nullable=True),
        sa.Column("anomaly_event_id", GUID(), nullable=True),
        sa.Column("window_start", UTCDateTime(), nullable=True),
        sa.Column("window_end", UTCDateTime(), nullable=True),
        sa.Column("predicted_class", sa.String(length=50), nullable=False),
        sa.Column("probabilities_json", JSONType(), nullable=True),
        sa.Column("confidence_value", sa.Float(), nullable=True),
        sa.Column("feature_snapshot_json", JSONType(), nullable=True),
        sa.Column("prediction_timestamp", UTCDateTime(), nullable=False),
        sa.Column("review_status", sa.String(length=20), server_default="pending", nullable=False),
        sa.ForeignKeyConstraint(["anomaly_event_id"], ["anomaly_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_id"], ["ml_models.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("review_status IN ('pending', 'confirmed', 'rejected')", name="ck_predictions_review"),
    )
    op.create_index("ix_ml_predictions_org_timestamp", "ml_predictions", ["organization_id", "prediction_timestamp"])
    op.create_index("ix_ml_predictions_equipment_timestamp", "ml_predictions", ["equipment_id", "prediction_timestamp"])
    op.create_index("ix_ml_predictions_model", "ml_predictions", ["model_id"])

    # 4. Knowledge Nodes
    op.create_table(
        "knowledge_nodes",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("node_type", sa.String(length=40), nullable=False),
        sa.Column("key", sa.String(length=150), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("equipment_type_id", GUID(), nullable=True),
        sa.Column("attributes_json", JSONType(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.Column("updated_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["equipment_type_id"], ["equipment_types.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_knowledge_nodes_key"),
    )
    op.create_index("ix_knowledge_nodes_node_type", "knowledge_nodes", ["node_type"])
    op.create_index("ix_knowledge_nodes_eq_type", "knowledge_nodes", ["equipment_type_id"])

    # 5. Knowledge Edges
    op.create_table(
        "knowledge_edges",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("source_node_id", GUID(), nullable=False),
        sa.Column("target_node_id", GUID(), nullable=False),
        sa.Column("relationship_type", sa.String(length=40), nullable=False),
        sa.Column("weight", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("attributes_json", JSONType(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["source_node_id"], ["knowledge_nodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_node_id"], ["knowledge_nodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_edges_source", "knowledge_edges", ["source_node_id"])
    op.create_index("ix_knowledge_edges_target", "knowledge_edges", ["target_node_id"])
    op.create_index("ix_knowledge_edges_type", "knowledge_edges", ["relationship_type"])

    # 6. Diagnoses
    op.create_table(
        "diagnoses",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("organization_id", GUID(), nullable=False),
        sa.Column("equipment_id", GUID(), nullable=False),
        sa.Column("primary_fault_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="possible_fault", nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("confidence_score", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("summary", sa.String(length=300), nullable=False),
        sa.Column("diagnostic_policy_version", sa.String(length=20), server_default="1.0", nullable=False),
        sa.Column("generated_at", UTCDateTime(), nullable=False),
        sa.Column("reviewed_by", GUID(), nullable=True),
        sa.Column("reviewed_at", UTCDateTime(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(length=20), server_default="pending", nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_fault_id"], ["faults.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_diagnoses_org_status_generated", "diagnoses", ["organization_id", "status", "generated_at"])
    op.create_index("ix_diagnoses_equipment_generated", "diagnoses", ["equipment_id", "generated_at"])
    op.create_index("ix_diagnoses_fault", "diagnoses", ["primary_fault_id"])

    # 7. Diagnosis Evidence
    op.create_table(
        "diagnosis_evidence",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("diagnosis_id", GUID(), nullable=False),
        sa.Column("evidence_type", sa.String(length=30), nullable=False),
        sa.Column("source_reference", sa.String(length=150), nullable=True),
        sa.Column("weight", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("details_json", JSONType(), nullable=False),
        sa.Column("created_at", UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["diagnosis_id"], ["diagnoses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_diagnosis_evidence_diagnosis", "diagnosis_evidence", ["diagnosis_id"])
    op.create_index("ix_diagnosis_evidence_type", "diagnosis_evidence", ["evidence_type"])


def downgrade() -> None:
    op.drop_table("diagnosis_evidence")
    op.drop_table("diagnoses")
    op.drop_table("knowledge_edges")
    op.drop_table("knowledge_nodes")
    op.drop_table("ml_predictions")
    op.drop_table("ml_models")
    op.drop_table("faults")

