"""merge npa and news heads

Revision ID: 7199923ff81c
Revises: 0013_npa_tracking_versions, 0015_news_dismissed_at
Create Date: 2026-09-06 21:06:04.516168
"""

from collections.abc import Sequence

revision: str = '7199923ff81c'
down_revision: str | None = ('0013_npa_tracking_versions', '0015_news_dismissed_at')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
