"""NewsRepo — NewsRepository over SQLAlchemy, a fresh session per call."""

import uuid

from common.core.db import async_session_factory
from common.core.logging import get_logger
from common.entities.news import NewsDTO
from common.schemas import News, Source
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from news_service.application.errors import NewsStoreError
from news_service.application.ports import NewsRepository, NewsTransaction
from news_service.infrastructure.repositories.news_transaction import SqlNewsTransaction

# What a failed write surfaces as: SQLAlchemy wraps driver errors, but a refused TCP
# connection from asyncpg can still escape as a bare OSError.
STORE_ERRORS = (SQLAlchemyError, OSError)

logger = get_logger(__name__)


async def _known_source_ids(session: AsyncSession, items: list[NewsDTO]) -> set[uuid.UUID]:
    wanted = {item.source_id for item in items}
    rows = await session.execute(select(Source.id).where(Source.id.in_(wanted)))
    return set(rows.scalars().all())


def _drop_orphans(items: list[NewsDTO], known: set[uuid.UUID]) -> list[NewsDTO]:
    """Skip items whose source is gone: a row needs its source, so the FK never fails the batch."""
    orphans = {item.source_id for item in items if item.source_id not in known}
    if orphans:
        logger.warning(
            "news sources gone, items skipped: ids=%s items=%d",
            sorted(map(str, orphans)),
            sum(item.source_id in orphans for item in items),
        )

    return [item for item in items if item.source_id not in orphans]


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

    async def add_many(self, items: list[NewsDTO]) -> int:
        if not items:
            return 0

        try:
            async with async_session_factory() as session:
                # A source deleted while the batch was in flight is skipped, not a failed
                # insert; a delete between the two statements only costs one nack + requeue.
                known = await _known_source_ids(session, items)
                rows = [item.model_dump() for item in _drop_orphans(items, known)]
                if not rows:
                    return 0

                # Urls already stored are skipped by the DB.
                stmt = insert(News).values(rows).on_conflict_do_nothing(index_elements=[News.url])
                result = await session.execute(stmt)
                await session.commit()
        except STORE_ERRORS as error:
            raise NewsStoreError(f"news batch insert failed: items={len(items)}") from error

        return result.rowcount

    async def mark_alert(self, news_id: uuid.UUID) -> News | None:
        async with self.begin() as transaction:
            news = await transaction.mark_alert(news_id)
            if news is not None:
                await transaction.commit()

            return news
