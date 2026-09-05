"""NewsRepo — NewsRepository over SQLAlchemy, a fresh session per call."""

import uuid

from common.core.db import async_session_factory
from common.entities.news import NewsDTO
from common.schemas import News
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from news_service.application.errors import NewsStoreError
from news_service.application.ports import NewsRepository

# What a failed write surfaces as: SQLAlchemy wraps driver errors, but a refused TCP
# connection from asyncpg can still escape as a bare OSError.
STORE_ERRORS = (SQLAlchemyError, OSError)


class NewsRepo(NewsRepository):
    """Each call runs in its own session (unit of work).

    No shared session state, so the same repo serves request handlers and the
    long-lived consumer concurrently.
    """

    async def list_all(self, limit: int, offset: int) -> list[News]:
        stmt = select(News).order_by(News.created_at.desc(), News.id).limit(limit).offset(offset)
        async with async_session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add_many(self, items: list[NewsDTO]) -> int:
        if not items:
            return 0

        # One statement, one transaction; urls already stored are skipped by the DB.
        stmt = (
            insert(News)
            .values([item.model_dump() for item in items])
            .on_conflict_do_nothing(index_elements=[News.url])
        )

        try:
            async with async_session_factory() as session:
                result = await session.execute(stmt)
                await session.commit()
        except STORE_ERRORS as error:
            raise NewsStoreError(f"news batch insert failed: items={len(items)}") from error

        return result.rowcount

    async def mark_alert(self, news_id: uuid.UUID) -> News | None:
        async with async_session_factory() as session:
            news = await session.get(News, news_id)
            if news is None:
                return None

            news.is_alert = True
            await session.commit()
            await session.refresh(news)
            return news
