"""News — DB-backed schema (SQLAlchemy ORM), owned by news_service.

Mirrors `domain.entities.news.NewsDTO` field for field: the consumer stores the bus
message as-is. `url` is unique — the same story is never stored twice. `is_alert` is
the one service-owned flag: false on insert, set true when a reader dismisses the item.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Uuid, func
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from domain.core.base import Base
from domain.entities.news import SourceType
from domain.entities.source import SourceReliability
from domain.schemas.types import SOURCE_RELIABILITY, SOURCE_TYPE

URL_MAX_LENGTH = 2048

# `sqlalchemy.text` is aliased because the model has a column named `text`.
_GEN_UUID = sql_text("gen_random_uuid()")
_EMPTY_JSON = sql_text("'{}'")


class News(Base):
    __tablename__ = "news"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, server_default=_GEN_UUID
    )
    schema_version: Mapped[int] = mapped_column(Integer)
    source_link: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[SourceType] = mapped_column(SOURCE_TYPE)
    source_reliability: Mapped[SourceReliability] = mapped_column(SOURCE_RELIABILITY)
    url: Mapped[str] = mapped_column(String(URL_MAX_LENGTH), unique=True)
    text: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=_EMPTY_JSON)
    is_alert: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
