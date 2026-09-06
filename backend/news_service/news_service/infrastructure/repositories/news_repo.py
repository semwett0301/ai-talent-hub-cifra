"""NewsRepo — NewsRepository over one SQLAlchemy `AsyncSession`."""

import uuid
from datetime import UTC, datetime

from common.core.logging import get_logger
from common.entities.news import NewsDTO
from common.schemas import News, Source
from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from news_service.application.dto.news import NewsQuery, NewsVisibility
from news_service.application.errors import NewsStoreError
from news_service.application.ports import NewsRepository

# What a failed write surfaces as: SQLAlchemy wraps driver errors, but a refused TCP
# connection from asyncpg can still escape as a bare OSError.
STORE_ERRORS = (SQLAlchemyError, OSError)
LIKE_ESCAPE = "\\"

logger = get_logger(__name__)


def _like_pattern(term: str) -> str:
    """`%term%` with LIKE's own wildcards in `term` neutralised."""
    escaped = term.replace(LIKE_ESCAPE, LIKE_ESCAPE * 2).replace("%", r"\%").replace("_", r"\_")
    return f"%{escaped}%"


def _filters(query: NewsQuery) -> list[ColumnElement[bool]]:
    clauses: list[ColumnElement[bool]] = []
    if query.visibility is NewsVisibility.VISIBLE:
        clauses.append(News.dismissed_at.is_(None))
    elif query.visibility is NewsVisibility.DISMISSED:
        clauses.append(News.dismissed_at.is_not(None))

    # An undated item counts from when it was collected.
    if query.since is not None:
        clauses.append(func.coalesce(News.published_at, News.created_at) >= query.since)

    if query.q:
        pattern = _like_pattern(query.q)
        clauses.append(
            or_(
                News.title.ilike(pattern, escape=LIKE_ESCAPE),
                News.text.ilike(pattern, escape=LIKE_ESCAPE),
            )
        )
    return clauses


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
    """Owns nothing: the session is opened and closed by whoever scopes the unit of work
    (`deps.get_news_repo` per request, `deps.BatchScope` per consumed batch)."""

    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def list_page(self, query: NewsQuery) -> list[News]:
        stmt = (
            select(News)
            .where(*_filters(query))
            .order_by(News.published_at.desc().nulls_last(), News.created_at.desc(), News.id)
            .limit(query.limit)
            .offset(query.offset)
        )
        return list((await self.__session.execute(stmt)).scalars().all())

    async def count(self, query: NewsQuery) -> int:
        stmt = select(func.count()).select_from(News).where(*_filters(query))
        return (await self.__session.execute(stmt)).scalar_one()

    async def get(self, news_id: uuid.UUID) -> News | None:
        return await self.__session.get(News, news_id)

    async def add_many(self, items: list[NewsDTO]) -> int:
        if not items:
            return 0

        try:
            # A source deleted while the batch was in flight is skipped, not a failed
            # insert; a delete between the two statements only costs one nack + requeue.
            rows = [
                item.model_dump()
                for item in _drop_orphans(items, await self.__known_sources(items))
            ]
            if not rows:
                return 0

            # Urls already stored are skipped by the DB.
            stmt = insert(News).values(rows).on_conflict_do_nothing(index_elements=[News.url])
            result = await self.__session.execute(stmt)
        except STORE_ERRORS as error:
            raise NewsStoreError(f"news batch insert failed: items={len(items)}") from error

        return result.rowcount

    async def mark_alert(self, news_id: uuid.UUID) -> News | None:
        news = await self.get(news_id)
        if news is None:
            return None

        news.is_alert = True
        await self.__session.flush()
        return news

    async def mark_dismissed(self, news_id: uuid.UUID) -> News | None:
        news = await self.get(news_id)
        if news is None:
            return None

        # A second dismiss keeps the original moment.
        if news.dismissed_at is None:
            news.dismissed_at = datetime.now(UTC)
            await self.__session.flush()
        return news

    async def mark_restored(self, news_id: uuid.UUID) -> News | None:
        news = await self.get(news_id)
        if news is None:
            return None

        news.dismissed_at = None
        await self.__session.flush()
        return news

    async def commit(self) -> None:
        try:
            await self.__session.commit()
        except STORE_ERRORS as error:
            raise NewsStoreError("news commit failed") from error

    async def __known_sources(self, items: list[NewsDTO]) -> set[uuid.UUID]:
        wanted = {item.source_id for item in items}
        rows = await self.__session.execute(select(Source.id).where(Source.id.in_(wanted)))
        return set(rows.scalars().all())
