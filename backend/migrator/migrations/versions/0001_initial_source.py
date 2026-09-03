"""initial source table

Revision ID: 0001_initial_source
Revises:
Create Date: 2026-09-03

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_source"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "type",
            sa.Enum("telegram", "rss", "web", native_enum=False, length=16, name="source_type"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("link", sa.String(length=1024), nullable=False),
        sa.Column("poll_interval_seconds", sa.Integer(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("source")
