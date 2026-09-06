"""news: persist event summaries and pgvector dedup state

Revision ID: 0018_news_event_dedup
Revises: 0017_npa_initial_summary_status
Create Date: 2026-09-06

The nullable columns preserve existing rows. New ingestion writes the summary, grounded
extraction, and normalized vector first; `event_cluster_id` remains null until the rest
of the batch passes the conservative membership pipeline.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR
from sqlalchemy.dialects import postgresql

revision: str = "0018_news_event_dedup"
down_revision: str | None = "0017_npa_initial_summary_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CLUSTER_INDEX = "ix_news_event_cluster_id"
EMBEDDING_INDEX = "ix_news_summary_embedding_hnsw"
EMBEDDING_DIMENSION = 1024


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("news", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column(
        "news",
        sa.Column("event_extraction", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "news", sa.Column("summary_embedding", VECTOR(EMBEDDING_DIMENSION), nullable=True)
    )
    op.add_column("news", sa.Column("event_cluster_id", sa.Uuid(), nullable=True))
    op.create_index(CLUSTER_INDEX, "news", ["event_cluster_id"])
    op.create_index(
        EMBEDDING_INDEX,
        "news",
        ["summary_embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"summary_embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index(EMBEDDING_INDEX, table_name="news")
    op.drop_index(CLUSTER_INDEX, table_name="news")
    op.drop_column("news", "event_cluster_id")
    op.drop_column("news", "summary_embedding")
    op.drop_column("news", "event_extraction")
    op.drop_column("news", "summary")
