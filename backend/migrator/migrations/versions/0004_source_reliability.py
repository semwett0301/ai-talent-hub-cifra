"""source: add reliability

Revision ID: 0004_source_reliability
Revises: 0003_source_uuid_id
Create Date: 2026-09-04

Adds `reliability` (`high` / `medium` / `low`), curated per source. Existing rows
default to `medium` via the server default.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_source_reliability"
down_revision: str | None = "0003_source_uuid_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "source",
        sa.Column(
            "reliability",
            sa.Enum(
                "high", "medium", "low", native_enum=False, length=8, name="source_reliability"
            ),
            server_default="medium",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("source", "reliability")
