"""news: `dismissed_at` — when a reader hid the item from the feed

Revision ID: 0015_news_dismissed_at
Revises: 0014_news_flat_shape
Create Date: 2026-09-06

Hiding gets its own column instead of riding on `is_alert`, which stays for the alert
semantics (an item escalated into a legislative act). Null = visible in the feed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_news_dismissed_at"
down_revision: str | None = "0014_news_flat_shape"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("news", sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("news", "dismissed_at")
