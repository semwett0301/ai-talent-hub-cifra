"""source: clear the poll interval on telegram sources and keep it clear

Revision ID: 0012_telegram_has_no_schedule
Revises: 0011_source_normalized_link
Create Date: 2026-09-06

Telegram is a push source: `SourceRegistry` subscribes to it and never schedules a
pull, so `poll_interval_seconds` on such a row is a value nothing reads. Rows created
before the API stopped accepting an interval on create carry one anyway; this clears
them and adds a CHECK so the column stays null for telegram regardless of who writes
the row — the same way `rss_link` is fenced to RSS.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_telegram_has_no_schedule"
down_revision: str | None = "0011_source_normalized_link"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CHECK_CONSTRAINT = "ck_source_telegram_has_no_interval"

source_table = sa.table(
    "source",
    sa.column("type", sa.String),
    sa.column("poll_interval_seconds", sa.Integer),
)


def upgrade() -> None:
    op.execute(
        source_table.update()
        .where(source_table.c.type == "telegram")
        .values(poll_interval_seconds=None)
    )
    op.create_check_constraint(
        CHECK_CONSTRAINT,
        "source",
        "type <> 'telegram' OR poll_interval_seconds IS NULL",
    )


def downgrade() -> None:
    op.drop_constraint(CHECK_CONSTRAINT, "source", type_="check")
