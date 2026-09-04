"""news: create the table news_service writes bus messages into

Revision ID: 0007_news_table
Revises: 0006_source_rss_link
Create Date: 2026-09-04

One row per `domain.entities.news.NewsDTO` consumed from the `news` exchange, stored
as-is. `url` is UNIQUE — the consumer inserts with ON CONFLICT DO NOTHING, so a story
delivered twice (or from two sources) lands once. `is_alert` (default false) is the
service-owned flag flipped by the dismiss endpoint.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_news_table"
down_revision: str | None = "0006_source_rss_link"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "news",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("source_link", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("source_reliability", sa.String(length=8), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "raw",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("is_alert", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )


def downgrade() -> None:
    op.drop_table("news")
