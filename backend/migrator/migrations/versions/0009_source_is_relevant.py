"""source: add is_relevant, enforce it stays disabled once not relevant

Revision ID: 0009_source_is_relevant
Revises: 0008_npa_table
Create Date: 2026-09-05

Adds `is_relevant` (default true) plus a CHECK constraint keeping a non-relevant
source always disabled too, regardless of who writes the row.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_source_is_relevant"
down_revision: str | None = "0008_npa_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "source", sa.Column("is_relevant", sa.Boolean(), nullable=False, server_default="true")
    )
    op.create_check_constraint(
        "ck_source_relevant_or_disabled",
        "source",
        "is_relevant OR NOT is_enabled",
    )


def downgrade() -> None:
    op.drop_constraint("ck_source_relevant_or_disabled", "source", type_="check")
    op.drop_column("source", "is_relevant")
