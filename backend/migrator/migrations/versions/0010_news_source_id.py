"""news: link each row to its source, nulled when the source is deleted

Revision ID: 0010_news_source_id
Revises: 0009_source_is_relevant
Create Date: 2026-09-06

Adds a nullable `source_id` FK to `source` with ON DELETE SET NULL: deleting a source
keeps its news, only detached. Existing rows stay NULL — the denormalized
`source_link` still says where they came from. Indexed so the cascade and per-source
filters never scan the table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_news_source_id"
down_revision: str | None = "0009_source_is_relevant"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FK_NAME = "fk_news_source_id_source"
INDEX_NAME = "ix_news_source_id"


def upgrade() -> None:
    op.add_column("news", sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(FK_NAME, "news", "source", ["source_id"], ["id"], ondelete="SET NULL")
    op.create_index(INDEX_NAME, "news", ["source_id"])


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="news")
    op.drop_constraint(FK_NAME, "news", type_="foreignkey")
    op.drop_column("news", "source_id")
