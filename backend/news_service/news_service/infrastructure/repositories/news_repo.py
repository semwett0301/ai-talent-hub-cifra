"""NewsRepo — NewsRepository over SQLAlchemy, a fresh session per call."""

import uuid

from common.core.db import async_session_factory
from common.schemas import News
from sqlalchemy import select

from news_service.application.ports import NewsRepository, NewsTransaction
from news_service.infrastructure.repositories.news_transaction import SqlNewsTransaction


class NewsRepo(NewsRepository):
    """Each call runs in its own session (unit of work).

    No shared session state, so the same repo serves request handlers and the
    long-lived consumer concurrently. `begin()` hands the caller a session to hold
    across several steps instead.
    """

    async def list_all(self, limit: int, offset: int) -> list[News]:
        stmt = select(News).order_by(News.created_at.desc(), News.id).limit(limit).offset(offset)
        async with async_session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())

    def begin(self) -> NewsTransaction:
        return SqlNewsTransaction(async_session_factory())

    async def mark_alert(self, news_id: uuid.UUID) -> News | None:
        async with self.begin() as transaction:
            news = await transaction.mark_alert(news_id)
            if news is not None:
                await transaction.commit()

            return news
