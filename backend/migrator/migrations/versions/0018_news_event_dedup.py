"""news: event summaries and pgvector dedup state, in their own table

Revision ID: 0018_news_event_dedup
Revises: 0017_npa_initial_summary_status
Create Date: 2026-09-06

`news_event_state` holds the dedup pipeline's own derived state for one news row —
separate from `news` (the source's unchanging facts) because this state is rewritten in
stages (summary → embedding → cluster assignment) while `news` itself never changes after
ingestion. `news_id` is both the primary key and the foreign key: one state row per news
row, created only once a summary exists. `event_cluster_id` remains null until the rest
of the batch passes the conservative membership pipeline.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR

revision: str = "0018_news_event_dedup"
down_revision: str | None = "0017_npa_initial_summary_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CLUSTER_INDEX = "ix_news_event_state_event_cluster_id"
EMBEDDING_INDEX = "ix_news_event_state_summary_embedding_hnsw"
EMBEDDING_DIMENSION = 1024


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "news_event_state",
        sa.Column("news_id", sa.Uuid(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("primary_event_found", sa.Boolean(), nullable=True),
        sa.Column("summary_embedding", VECTOR(EMBEDDING_DIMENSION), nullable=True),
        sa.Column("event_cluster_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["news_id"], ["news.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("news_id"),
    )
    op.create_index(CLUSTER_INDEX, "news_event_state", ["event_cluster_id"])
    op.create_index(
        EMBEDDING_INDEX,
        "news_event_state",
        ["summary_embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"summary_embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index(EMBEDDING_INDEX, table_name="news_event_state")
    op.drop_index(CLUSTER_INDEX, table_name="news_event_state")
    op.drop_table("news_event_state")
