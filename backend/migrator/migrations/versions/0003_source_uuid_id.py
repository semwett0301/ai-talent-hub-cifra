"""source: uuid surrogate id, shrink link to varchar(255)

Revision ID: 0003_source_uuid_id
Revises: 0002_seed_sources
Create Date: 2026-09-04

Adds a DB-generated UUID primary key (gen_random_uuid(), built into Postgres
since 13 — no extension needed) and shrinks link, which is data, not identity.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_source_uuid_id"
down_revision: str | None = "0002_seed_sources"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("source_pkey", "source", type_="primary")
    op.drop_column("source", "id")
    op.add_column(
        "source",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
    )
    op.create_primary_key("source_pkey", "source", ["id"])
    op.alter_column("source", "link", type_=sa.String(length=255), existing_type=sa.String(1024))


def downgrade() -> None:
    op.drop_constraint("source_pkey", "source", type_="primary")
    op.drop_column("source", "id")
    op.alter_column("source", "link", type_=sa.String(length=1024), existing_type=sa.String(255))
    op.add_column("source", sa.Column("id", sa.Integer(), sa.Identity(), nullable=False))
    op.create_primary_key("source_pkey", "source", ["id"])
