"""source: add rss_link, attach feed links to seeded sources

Revision ID: 0006_source_rss_link
Revises: 0005_seed_test_source
Create Date: 2026-09-04

Adds `rss_link`, the discovered feed URL for RSS sources (scraping-only, never
exposed via the API). A CHECK constraint enforces it stays null for any source
whose `type` isn't `rss`, regardless of who writes the row.

Also backfills it for three of the sites seeded by `0002_seed_sources` —
vedomosti, kommersant and cableman, whose `link` was just the site homepage, not
a feed. Telesputnik has no known feed, so its `type` switches to `web` instead.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_source_rss_link"
down_revision: str | None = "0005_seed_test_source"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

VEDOMOSTI_LINK = "https://www.vedomosti.ru"
VEDOMOSTI_RSS_LINK = "https://www.vedomosti.ru/rss/news"
KOMMERSANT_LINK = "https://www.kommersant.ru"
KOMMERSANT_RSS_LINK = "https://www.kommersant.ru/rss/main.xml"
CABLEMAN_LINK = "https://www.cableman.ru/"
CABLEMAN_RSS_LINK = "https://www.cableman.ru/taxonomy/term/7413/feed"
TELESPUTNIK_LINK = "https://telesputnik.ru"

source_table = sa.table(
    "source",
    sa.column("type", sa.String),
    sa.column("link", sa.String),
    sa.column("rss_link", sa.String),
)


def upgrade() -> None:
    op.add_column("source", sa.Column("rss_link", sa.String(length=255), nullable=True))
    op.create_check_constraint(
        "ck_source_rss_link_only_for_rss",
        "source",
        "type = 'rss' OR rss_link IS NULL",
    )

    op.execute(
        source_table.update()
        .where(source_table.c.link == VEDOMOSTI_LINK)
        .values(rss_link=VEDOMOSTI_RSS_LINK)
    )
    op.execute(
        source_table.update()
        .where(source_table.c.link == KOMMERSANT_LINK)
        .values(rss_link=KOMMERSANT_RSS_LINK)
    )
    op.execute(
        source_table.update()
        .where(source_table.c.link == CABLEMAN_LINK)
        .values(rss_link=CABLEMAN_RSS_LINK)
    )
    op.execute(
        source_table.update().where(source_table.c.link == TELESPUTNIK_LINK).values(type="web")
    )


def downgrade() -> None:
    op.execute(
        source_table.update().where(source_table.c.link == TELESPUTNIK_LINK).values(type="rss")
    )

    op.drop_constraint("ck_source_rss_link_only_for_rss", "source", type_="check")
    op.drop_column("source", "rss_link")
