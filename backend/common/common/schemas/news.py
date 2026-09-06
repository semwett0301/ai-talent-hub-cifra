"""News — DB-backed schema (SQLAlchemy ORM), owned by news_service.

Mirrors `common.entities.news.NewsDTO` field for field: the consumer stores the bus
message as-is, one flat row. `url` is unique — the same story is never stored twice.
`source_id` points at the `source` row and the news goes with it when that source is
deleted. Two service-owned fields: `dismissed_at` (a reader hid the item from the feed) and
`is_alert` (the item was escalated into a legislative act). A summary and extraction are
persisted before its vector, and `event_cluster_id` is filled only after membership
validation (see `news_service.application.services.news_deduplicator`).
"""

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from common.core.db import Base
from common.entities.news import SourceType
from common.entities.source import SourceReliability
from common.schemas.types import SOURCE_RELIABILITY, SOURCE_TYPE

URL_MAX_LENGTH = 2048
SUMMARY_EMBEDDING_DIMENSION = 1024
SUMMARY_EMBEDDING_INDEX = "ix_news_summary_embedding_hnsw"

# `sqlalchemy.text` is aliased because the model has a column named `text`.
_GEN_UUID = sql_text("gen_random_uuid()")
_EMPTY_ARRAY = sql_text("'{}'")


class News(Base):
    __tablename__ = "news"
    __table_args__ = (
        Index(
            SUMMARY_EMBEDDING_INDEX,
            "summary_embedding",
            postgresql_using="hnsw",
            postgresql_ops={"summary_embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, server_default=_GEN_UUID
    )
    schema_version: Mapped[int] = mapped_column(Integer)

    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("source.id", ondelete="CASCADE"), index=True
    )
    source_link: Mapped[str] = mapped_column(String(255))
    source_name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[SourceType] = mapped_column(SOURCE_TYPE)
    source_reliability: Mapped[SourceReliability] = mapped_column(SOURCE_RELIABILITY)
    # One array column, no index: tags differ per item and are never filtered on.
    source_tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=_EMPTY_ARRAY
    )

    url: Mapped[str] = mapped_column(String(URL_MAX_LENGTH), unique=True)
    # No length cap: a long first sentence is stored whole, the UI truncates.
    title: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_extraction: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, deferred=True
    )
    summary_embedding: Mapped[list[float] | None] = mapped_column(
        VECTOR(SUMMARY_EMBEDDING_DIMENSION), nullable=True, deferred=True
    )
    event_cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True, index=True
    )

    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_alert: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
