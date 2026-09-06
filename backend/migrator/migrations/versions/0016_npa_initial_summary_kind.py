"""npa: distinguish initial document overviews from revision comparisons

Revision ID: 0016_npa_initial_summary_kind
Revises: 7199923ff81c
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_npa_initial_summary_kind"
down_revision: str | None = "7199923ff81c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("npa", sa.Column("summary_kind", sa.String(length=16), nullable=True))
    op.add_column("npa_version", sa.Column("summary_kind", sa.String(length=16), nullable=True))
    op.execute("UPDATE npa SET summary_kind = 'change' WHERE summary IS NOT NULL")
    op.execute("UPDATE npa_version SET summary_kind = 'change' WHERE summary IS NOT NULL")


def downgrade() -> None:
    op.drop_column("npa_version", "summary_kind")
    op.drop_column("npa", "summary_kind")
