"""News — DB-backed schema (SQLAlchemy ORM), owned by news_service.

Mirrors `common.entities.news.NewsDTO` field for field: the consumer stores the bus
message as-is, one flat row. `url` is unique — the same story is never stored twice.
`source_id` points at the `source` row and the news goes with it when that source is
deleted. Two service-owned fields: `dismissed_at` (a reader hid the item from the feed) and
`is_alert` (the item was escalated into a legislative act). The dedup pipeline's own derived
state (summary, extraction, embedding, cluster assignment) lives in `NewsEventState`, read
here through the `event_state` relationship only.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.core.db import Base
from common.entities.news import SourceType
from common.entities.source import SourceReliability
from common.schemas.types import SOURCE_RELIABILITY, SOURCE_TYPE

if TYPE_CHECKING:
    from common.schemas.news_cluster_ranking import NewsClusterRanking
    from common.schemas.news_event_state import NewsEventState

URL_MAX_LENGTH = 2048

# `sqlalchemy.text` is aliased because the model has a column named `text`.
_GEN_UUID = sql_text("gen_random_uuid()")
_EMPTY_ARRAY = sql_text("'{}'")


class News(Base):
    __tablename__ = "news"

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

    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_alert: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Read-only view of the pipeline's state; loaded with the row so the API never lazy-loads.
    event_state: Mapped["NewsEventState | None"] = relationship(
        "NewsEventState", uselist=False, viewonly=True, lazy="joined"
    )
    # The cluster's relevance hangs on its head row (cluster_id == news.id): None on a duplicate.
    cluster_ranking: Mapped["NewsClusterRanking | None"] = relationship(
        "NewsClusterRanking", uselist=False, viewonly=True, lazy="joined"
    )

    @property
    def summary(self) -> str | None:
        return self.event_state.summary if self.event_state else None

    @property
    def event_cluster_id(self) -> uuid.UUID | None:
        return self.event_state.event_cluster_id if self.event_state else None
