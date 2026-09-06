"""RssLink — one feed URL of an RSS source (DB-backed schema, SQLAlchemy ORM).

A source can serve several feeds (sections, tags, comments); `SourceService` stores
the ones auto-detection found, and `RssCollector` polls them all. Rows exist only for
`type=rss` sources — a DB trigger refuses any other, regardless of who writes the row.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from common.core.db import Base

URL_MAX_LENGTH = 2048


class RssLink(Base):
    __tablename__ = "rss_link"
    __table_args__ = (UniqueConstraint("source_id", "url", name="uq_rss_link_source_url"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("source.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(String(URL_MAX_LENGTH))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
