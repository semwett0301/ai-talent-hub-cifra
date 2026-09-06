"""news: persist one relevance result per event cluster

Revision ID: 0012_news_cluster_ranking
Revises: 0011_news_event_dedup
Create Date: 2026-09-06

Generated with Alembic autogenerate, then reviewed to remove unrelated legacy
nullability drift on the source timestamps.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_news_cluster_ranking"
down_revision: str | None = "0011_news_event_dedup"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RANKING_SCORE_INDEX = "ix_news_cluster_ranking_relevance_score"


def upgrade() -> None:
    op.create_table(
        "news_cluster_ranking",
        sa.Column("cluster_id", sa.Uuid(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("context_score", sa.Float(), nullable=False),
        sa.Column("member_count", sa.Integer(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "ranked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["cluster_id"], ["news.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("cluster_id"),
    )
    op.create_index(
        RANKING_SCORE_INDEX,
        "news_cluster_ranking",
        ["relevance_score"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(RANKING_SCORE_INDEX, table_name="news_cluster_ranking")
    op.drop_table("news_cluster_ranking")
