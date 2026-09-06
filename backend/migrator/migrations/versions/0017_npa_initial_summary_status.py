"""npa: track asynchronous initial overview generation

Revision ID: 0017_npa_initial_summary_status
Revises: 0016_npa_initial_summary_kind
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_npa_initial_summary_status"
down_revision: str | None = "0016_npa_initial_summary_kind"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("npa", sa.Column("initial_summary_status", sa.String(length=16), nullable=True))
    op.execute("UPDATE npa SET initial_summary_status = 'ready' WHERE summary_kind = 'initial'")


def downgrade() -> None:
    op.drop_column("npa", "initial_summary_status")
