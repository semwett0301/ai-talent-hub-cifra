"""NewsRepo — NewsRepository over one SQLAlchemy `AsyncSession`."""

import uuid
from datetime import UTC, datetime

from common.core.logging import get_logger
from common.entities.news import NewsDTO
from common.schemas import News, NewsClusterRanking, NewsEventState, Source
from sqlalchemy import ColumnElement, Select, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from news_service.application.dto.news import NewsQuery, NewsVisibility
from news_service.application.errors import NewsStoreError
from news_service.application.ports import NewsRepository
from news_service.domain.event_cluster import RelevanceCategory

# What a failed write surfaces as: SQLAlchemy wraps driver errors, but a refused TCP
# connection from asyncpg can still escape as a bare OSError.
STORE_ERRORS = (SQLAlchemyError, OSError)
LIKE_ESCAPE = "\\"
# One item per event: a duplicate points at another item's cluster and is left out; an item
# the dedup stage has not reached yet (no cluster) still shows.
IS_CLUSTER_HEAD = or_(
    NewsEventState.event_cluster_id.is_(None), NewsEventState.event_cluster_id == News.id
)
# The feed shows only what the ranker has judged relevant: unranked items and low-relevance
# clusters never reach the reader. The alerts tab (`is_alert=true`) is exempt — see `_gates`.
SHOWN_CATEGORIES = tuple(
    category.value for category in RelevanceCategory if category is not RelevanceCategory.LOW
)
IS_RANKED_RELEVANT = NewsClusterRanking.category.in_(SHOWN_CATEGORIES)

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

    if query.is_alert is not None:
        clauses.append(News.is_alert.is_(query.is_alert))

    if query.q:
        pattern = _like_pattern(query.q)
        clauses.append(
            or_(
                News.title.ilike(pattern, escape=LIKE_ESCAPE),
                News.text.ilike(pattern, escape=LIKE_ESCAPE),
            )
        )
    return clauses


def _gates(query: NewsQuery) -> list[ColumnElement[bool]]:
    """One row per event always; only ranked-relevant rows unless the alerts tab is asked for —
    an alert is its own signal and shows whatever the ranker made of it."""
    if query.is_alert is True:
        return [IS_CLUSTER_HEAD]
    return [IS_CLUSTER_HEAD, IS_RANKED_RELEVANT]


def _feed_statement(query: NewsQuery) -> Select[tuple[News]]:
    """The feed's rows with dedup state and ranking loaded in the same query."""
    return (
        select(News)
        .outerjoin(News.event_state)
        .outerjoin(News.cluster_ranking)
        .options(contains_eager(News.event_state), contains_eager(News.cluster_ranking))
        .where(*_filters(query), *_gates(query))
        .order_by(News.published_at.desc().nulls_last(), News.created_at.desc(), News.id)
    )


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

    async def list_matching(self, query: NewsQuery) -> list[News]:
        rows = await self.__session.execute(_feed_statement(query))
        return list(rows.scalars().all())

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
