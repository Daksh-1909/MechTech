"""add audit logs

Revision ID: 87c9ef022ec2
Revises: 05e9a2ea95ec
Create Date: 2026-11-05 12:52:15.440873

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.types import UTCDateTime

revision: str = "87c9ef022ec2"
down_revision: str | Sequence[str] | None = "05e9a2ea95ec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("timestamp", UTCDateTime(timezone=True), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("audit_logs", schema=None) as batch_op:
        batch_op.create_index("ix_audit_logs_action", ["action"], unique=False)
        batch_op.create_index(
            "ix_audit_logs_resource",
            ["resource_type", "resource_id"],
            unique=False,
        )
        batch_op.create_index("ix_audit_logs_timestamp", ["timestamp"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("audit_logs", schema=None) as batch_op:
        batch_op.drop_index("ix_audit_logs_timestamp")
        batch_op.drop_index("ix_audit_logs_resource")
        batch_op.drop_index("ix_audit_logs_action")

    op.drop_table("audit_logs")
