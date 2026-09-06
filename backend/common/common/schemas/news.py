"""News — DB-backed schema (SQLAlchemy ORM), owned by news_service.

Stores `common.entities.news.NewsDTO` plus the staged dedup state. `url` is unique;
`source_id` is nulled when its source is deleted. A summary and extraction are persisted
before its vector, and `event_cluster_id` is filled only after membership validation.
"""

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import JSONB
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
_EMPTY_JSON = sql_text("'{}'")


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
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("source.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_link: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[SourceType] = mapped_column(SOURCE_TYPE)
    source_reliability: Mapped[SourceReliability] = mapped_column(SOURCE_RELIABILITY)
    url: Mapped[str] = mapped_column(String(URL_MAX_LENGTH), unique=True)
    text: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=_EMPTY_JSON)
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
    is_alert: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
