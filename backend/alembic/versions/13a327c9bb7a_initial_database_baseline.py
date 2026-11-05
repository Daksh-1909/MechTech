"""Initial database baseline.

Revision ID: 13a327c9bb7a
Revises:
Create Date: 2026-11-05 01:52:49.228407

The first schema tables are introduced by later migrations. This baseline
records the Alembic starting point so fresh databases have a migration head.
"""

from collections.abc import Sequence

revision: str = "13a327c9bb7a"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the baseline revision (no schema changes yet)."""


def downgrade() -> None:
    """Remove the baseline revision (no schema changes yet)."""
