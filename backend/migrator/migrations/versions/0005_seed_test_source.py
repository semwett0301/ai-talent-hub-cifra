"""seed the Тест telegram source

Revision ID: 0005_seed_test_source
Revises: 0004_source_reliability
Create Date: 2026-09-04

Adds one throwaway Telegram channel used for manual end-to-end checks. Telegram
is a push source, so `poll_interval_seconds` stays null; `reliability` is `low`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_seed_test_source"
down_revision: str | None = "0004_source_reliability"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TEST_SOURCE_NAME = "Тест"
TEST_SOURCE_LINK = "https://t.me/dsadsascx"

# Inline table — only the columns we set; id/is_enabled/timestamps use DB defaults.
source_table = sa.table(
    "source",
    sa.column("type", sa.String),
    sa.column("name", sa.String),
    sa.column("link", sa.String),
    sa.column("reliability", sa.String),
)


def upgrade() -> None:
    op.bulk_insert(
        source_table,
        [
            {
                "type": "telegram",
                "name": TEST_SOURCE_NAME,
                "link": TEST_SOURCE_LINK,
                "reliability": "low",
            }
        ],
    )


def downgrade() -> None:
    op.execute(source_table.delete().where(source_table.c.link == TEST_SOURCE_LINK))
