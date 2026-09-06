"""Source — DB-backed schema (SQLAlchemy ORM), owned by source_service."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from common.core.db import Base
from common.entities.news import SourceType
from common.entities.source import SourceReliability
from common.schemas.types import SOURCE_RELIABILITY, SOURCE_TYPE


class Source(Base):
    __tablename__ = "source"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    type: Mapped[SourceType] = mapped_column(SOURCE_TYPE)
    name: Mapped[str] = mapped_column(String(255))
    link: Mapped[str] = mapped_column(String(255))
    # Same address spelled differently is the same source; set from `link`, never by a client.
    normalized_link: Mapped[str] = mapped_column(String(255), unique=True)
    # Feed URL for RSS sources only; DB-enforced by a CHECK constraint, not the app.
    rss_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reliability: Mapped[SourceReliability] = mapped_column(
        SOURCE_RELIABILITY, default=SourceReliability.MEDIUM, server_default="medium"
    )
    # How often to poll a pull source (RSS/Web), seconds. Null for push (Telegram).
    poll_interval_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    # False once a WEB crawl finds nothing; keeps is_enabled false too, by CHECK constraint.
    is_relevant: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
