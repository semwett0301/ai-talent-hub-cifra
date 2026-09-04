"""seed initial sources

Revision ID: 0002_seed_sources
Revises: 0001_initial_source
Create Date: 2026-09-04

Seeds the starting source list (Telegram channels collected as TG, sites as RSS).
Per the migrator rule, the table is defined inline (`sa.table`) — never import
service models, the runtime image has no service package.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_seed_sources"
down_revision: str | None = "0001_initial_source"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Poll every 15 minutes for all seeds (per the source-list note).
POLL_INTERVAL_SECONDS = 15 * 60

# (type, link, name). Telegram channels -> "telegram", news sites -> "rss".
SEED_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("telegram", "https://t.me/cit_gov", "Цифровые индустриальные технологии - дайджест"),
    ("telegram", "https://t.me/rfrit", "РФРИТ"),
    ("telegram", "https://t.me/grantsforbussines", "Гранты для ИТ"),
    ("telegram", "https://t.me/cio_channel", "CIO: канал IT руководителей"),
    ("telegram", "https://t.me/rustorgpred", "Торгпред - тендеры и закупки"),
    ("telegram", "https://t.me/government_rus", "Правительство РФ - сводки"),
    ("telegram", "https://t.me/arperf", "АРПЭ - новости"),
    ("telegram", "https://t.me/icipr", "ЦИПР - новости и анонсы мероприятий"),
    ("telegram", "https://t.me/arppsoft", "АРПП - новости"),
    ("rss", "https://www.vedomosti.ru", "Ведомости"),
    ("rss", "https://www.kommersant.ru", "Коммерсант"),
    ("rss", "https://www.cableman.ru/", "Кабельщик"),
    ("rss", "https://telesputnik.ru", "Телеспутник"),
)

# Inline table — only the columns we set; id/is_enabled/timestamps use DB defaults.
source_table = sa.table(
    "source",
    sa.column("type", sa.String),
    sa.column("name", sa.String),
    sa.column("link", sa.String),
    sa.column("poll_interval_seconds", sa.Integer),
)


def upgrade() -> None:
    op.bulk_insert(
        source_table,
        [
            {
                "type": source_type,
                "link": link,
                "name": name,
                "poll_interval_seconds": POLL_INTERVAL_SECONDS,
            }
            for source_type, link, name in SEED_SOURCES
        ],
    )


def downgrade() -> None:
    links = [link for _, link, _ in SEED_SOURCES]
    op.execute(source_table.delete().where(source_table.c.link.in_(links)))
