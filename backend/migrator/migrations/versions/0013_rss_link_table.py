"""rss_link: one-to-many feed URLs per source, replacing source.rss_link

Revision ID: 0013_rss_link_table
Revises: 0012_telegram_has_no_schedule
Create Date: 2026-09-06

A site can serve several feeds, and auto-detection now keeps every one it finds. The
single `source.rss_link` column moves into an `rss_link` table (`source_id` FK with
ON DELETE CASCADE, `(source_id, url)` UNIQUE), existing values are carried over, and
the old CHECK gives way to a trigger: an `rss_link` row is refused unless its source
is `type = 'rss'` — the same fence, now on a child table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_rss_link_table"
down_revision: str | None = "0012_telegram_has_no_schedule"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "rss_link"
FK_NAME = "fk_rss_link_source_id_source"
INDEX_NAME = "ix_rss_link_source_id"
UNIQUE_NAME = "uq_rss_link_source_url"
TRIGGER_FUNCTION = "rss_link_requires_rss_source"
TRIGGER = "trg_rss_link_requires_rss_source"
OLD_CHECK = "ck_source_rss_link_only_for_rss"
URL_MAX_LENGTH = 2048

CREATE_TRIGGER_FUNCTION = f"""
CREATE FUNCTION {TRIGGER_FUNCTION}() RETURNS trigger AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM source WHERE id = NEW.source_id AND type = 'rss') THEN
        RAISE EXCEPTION 'rss_link refused: source % is not of type rss (url %)',
            NEW.source_id, NEW.url
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

CREATE_TRIGGER = f"""
CREATE TRIGGER {TRIGGER}
BEFORE INSERT OR UPDATE OF source_id ON {TABLE}
FOR EACH ROW EXECUTE FUNCTION {TRIGGER_FUNCTION}();
"""

# Old column → new rows, and back (downgrade keeps one feed per source: the first by url).
COPY_LINKS_TO_TABLE = f"""
INSERT INTO {TABLE} (source_id, url)
SELECT id, rss_link FROM source WHERE rss_link IS NOT NULL;
"""
COPY_LINKS_TO_COLUMN = f"""
UPDATE source SET rss_link = first_feed.url
FROM (
    SELECT DISTINCT ON (source_id) source_id, url FROM {TABLE} ORDER BY source_id, url
) AS first_feed
WHERE source.id = first_feed.source_id;
"""


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(length=URL_MAX_LENGTH), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("source_id", "url", name=UNIQUE_NAME),
    )
    op.create_foreign_key(FK_NAME, TABLE, "source", ["source_id"], ["id"], ondelete="CASCADE")
    op.create_index(INDEX_NAME, TABLE, ["source_id"])

    op.execute(CREATE_TRIGGER_FUNCTION)
    op.execute(CREATE_TRIGGER)

    op.execute(COPY_LINKS_TO_TABLE)
    op.drop_constraint(OLD_CHECK, "source", type_="check")
    op.drop_column("source", "rss_link")


def downgrade() -> None:
    op.add_column("source", sa.Column("rss_link", sa.String(length=255), nullable=True))
    op.execute(COPY_LINKS_TO_COLUMN)
    op.create_check_constraint(OLD_CHECK, "source", "type = 'rss' OR rss_link IS NULL")

    op.execute(f"DROP TRIGGER {TRIGGER} ON {TABLE}")
    op.execute(f"DROP FUNCTION {TRIGGER_FUNCTION}()")
    op.drop_table(TABLE)
