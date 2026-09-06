"""npa: store an AI-generated plain-language title.

Revision ID: 0018_npa_plain_title
Revises: 0017_npa_initial_summary_status
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018_npa_plain_title"
down_revision: str | None = "0017_npa_initial_summary_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("npa", sa.Column("plain_title", sa.String(length=90), nullable=True))


def downgrade() -> None:
    op.drop_column("npa", "plain_title")
