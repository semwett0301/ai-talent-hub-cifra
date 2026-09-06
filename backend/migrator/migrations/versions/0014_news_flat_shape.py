"""news: one flat typed row instead of the per-collector `raw` blob

Revision ID: 0014_news_flat_shape
Revises: 0013_rss_link_table
Create Date: 2026-09-06

`NewsDTO` v5 carries what every collector can say about an item as typed fields —
`title`, `excerpt`, `updated_at`, `source_name`, `source_tags` — and drops
`raw`, whose keys differed per source type. A row now needs its source: `source_id`
becomes NOT NULL with ON DELETE CASCADE. Existing rows are backfilled from what `raw`
held (RSS `title`/`summary`, Web `title`/`description`/`modified_at`/`section`);
a Telegram row gets its first sentence as `title` and its hashtags as tags — the same
expressions `TelegramCollector` applies, copied into SQL rather than imported so the
revision keeps applying the same way. Orphans are re-linked by `source_link` first; the
ones whose source is gone are deleted.

Downgrade is lossy: `raw` comes back empty, the crawler's provenance is gone.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_news_flat_shape"
down_revision: str | None = "0013_rss_link_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FK_NAME = "fk_news_source_id_source"
NAME_MAX_LENGTH = 255
NEW_SCHEMA_VERSION = 5
OLD_SCHEMA_VERSION = 4

# Rows detached before this revision still name their source by link.
RELINK_ORPHANS = """
UPDATE news SET source_id = s.id
FROM source s
WHERE news.source_id IS NULL AND s.link = news.source_link;
"""
DELETE_ORPHANS = "DELETE FROM news WHERE source_id IS NULL;"

# `title`: the collector's, else the first sentence (Telegram), else the text itself — the
# same fallback chain `TelegramCollector` applies.
BACKFILL_FROM_RAW = r"""
UPDATE news SET
    title = COALESCE(
        NULLIF(raw->>'title', ''),
        NULLIF(trim(substring(text from '^\s*[^.!?\n]+[.!?]?')), ''),
        text
    ),
    excerpt = COALESCE(NULLIF(raw->>'summary', ''), NULLIF(raw->>'description', '')),
    updated_at = CAST(NULLIF(raw->>'modified_at', '') AS timestamptz);
"""
BACKFILL_SOURCE_NAME = """
UPDATE news SET source_name = s.name
FROM source s
WHERE s.id = news.source_id;
"""
# Web kept its rubric under `section`; Telegram tags are the post's hashtags; RSS
# categories were never stored, so those rows stay empty.
BACKFILL_TAGS = r"""
UPDATE news SET source_tags = CASE
    WHEN NULLIF(raw->>'section', '') IS NOT NULL THEN ARRAY[raw->>'section']
    WHEN source_type = 'telegram'
        THEN ARRAY(SELECT DISTINCT m[1] FROM regexp_matches(text, '#(\w+)', 'g') m)
    ELSE '{}'
END;
"""


def _add_flat_columns() -> None:
    op.add_column("news", sa.Column("title", sa.Text(), nullable=True))
    op.add_column("news", sa.Column("excerpt", sa.Text(), nullable=True))
    op.add_column("news", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("news", sa.Column("source_name", sa.String(NAME_MAX_LENGTH), nullable=True))
    op.add_column(
        "news",
        sa.Column(
            "source_tags",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
    )


def _require_source(ondelete: str, nullable: bool) -> None:
    op.alter_column("news", "source_id", nullable=nullable)
    op.drop_constraint(FK_NAME, "news", type_="foreignkey")
    op.create_foreign_key(FK_NAME, "news", "source", ["source_id"], ["id"], ondelete=ondelete)


def upgrade() -> None:
    op.execute(RELINK_ORPHANS)
    op.execute(DELETE_ORPHANS)

    _add_flat_columns()
    op.execute(BACKFILL_FROM_RAW)
    op.execute(BACKFILL_SOURCE_NAME)
    op.execute(BACKFILL_TAGS)

    op.alter_column("news", "title", nullable=False)
    op.alter_column("news", "source_name", nullable=False)
    _require_source(ondelete="CASCADE", nullable=False)

    op.execute(f"UPDATE news SET schema_version = {NEW_SCHEMA_VERSION};")
    op.drop_column("news", "raw")


def downgrade() -> None:
    op.add_column(
        "news",
        sa.Column(
            "raw",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
    )
    op.execute(f"UPDATE news SET schema_version = {OLD_SCHEMA_VERSION};")

    _require_source(ondelete="SET NULL", nullable=True)
    for column in ("source_tags", "source_name", "updated_at", "excerpt", "title"):
        op.drop_column("news", column)
