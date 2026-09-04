"""source: link as primary key instead of id

Revision ID: 0003_source_link_pk
Revises: 0002_seed_sources
Create Date: 2026-09-04

A source is naturally identified by its link (URL/channel), so the surrogate
integer id is dropped in favor of it. Existing rows already have unique links
(seeded in 0002), so this is a straight swap.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_source_link_pk"
down_revision: str | None = "0002_seed_sources"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("source_pkey", "source", type_="primary")
    op.drop_column("source", "id")
    op.create_primary_key("source_pkey", "source", ["link"])


def downgrade() -> None:
    op.drop_constraint("source_pkey", "source", type_="primary")
    op.add_column("source", sa.Column("id", sa.Integer(), sa.Identity(), nullable=False))
    op.create_primary_key("source_pkey", "source", ["id"])
