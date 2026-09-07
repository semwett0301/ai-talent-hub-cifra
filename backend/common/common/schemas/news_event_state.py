"""NewsEventState — the dedup pipeline's own derived state for one news row.

One row per `news` row, created once a summary exists. Kept separate from `News` (the
source's unchanging facts) because this state is rewritten in stages by the dedup
pipeline (summary → embedding → cluster assignment) while `News` itself never changes
after ingestion.
"""

import uuid

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Boolean, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from common.core.db import Base

SUMMARY_EMBEDDING_DIMENSION = 1024
SUMMARY_EMBEDDING_INDEX = "ix_news_event_state_summary_embedding_hnsw"


class NewsEventState(Base):
    __tablename__ = "news_event_state"
    __table_args__ = (
        Index(
            SUMMARY_EMBEDDING_INDEX,
            "summary_embedding",
            postgresql_using="hnsw",
            postgresql_ops={"summary_embedding": "vector_cosine_ops"},
        ),
    )

    news_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("news.id", ondelete="CASCADE"),
        primary_key=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_event_found: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    summary_embedding: Mapped[list[float] | None] = mapped_column(
        VECTOR(SUMMARY_EMBEDDING_DIMENSION), nullable=True, deferred=True
    )
    event_cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True, index=True
    )
