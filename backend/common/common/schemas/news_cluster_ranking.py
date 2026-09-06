"""One persisted relevance result for one deduplicated news cluster."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from common.core.db import Base

CATEGORY_MAX_LENGTH = 32


class NewsClusterRanking(Base):
    __tablename__ = "news_cluster_ranking"

    cluster_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("news.id", ondelete="CASCADE"),
        primary_key=True,
    )
    relevance_score: Mapped[float] = mapped_column(Float, index=True)
    category: Mapped[str] = mapped_column(String(CATEGORY_MAX_LENGTH))
    context_score: Mapped[float] = mapped_column(Float)
    member_count: Mapped[int] = mapped_column(Integer)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB)
    ranked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
