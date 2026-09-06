"""PostgreSQL/pgvector persistence for summarized-news event deduplication."""

import uuid
from collections import defaultdict
from datetime import timedelta
from typing import cast

from common.core.db import async_session_factory
from common.core.logging import get_logger
from common.schemas import News, Source
from sqlalchemy import Table, bindparam, desc, func, literal, or_, select, update
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from news_service.application.errors import NewsStoreError
from news_service.application.ports import DedupRepository
from news_service.domain.dedup import (
    CandidateCluster,
    CandidateQuery,
    ClusterAssignment,
    EventSummary,
    PreparedNews,
    StoredNewsState,
)

STORE_ERRORS = (SQLAlchemyError, OSError)

logger = get_logger(__name__)


class SqlDedupRepository(DedupRepository):
    async def list_states(self, urls: list[str]) -> dict[str, StoredNewsState]:
        if not urls:
            return {}
        has_summary = News.summary.is_not(None) & News.event_extraction.is_not(None)
        statement = select(News.id, News.url, has_summary).where(News.url.in_(urls))
        try:
            async with async_session_factory() as session:
                rows = (await session.execute(statement)).all()
        except STORE_ERRORS as error:
            raise NewsStoreError(f"news states query failed: urls={len(urls)}") from error
        return {row.url: StoredNewsState(row.id, row[2]) for row in rows}

    async def save_summaries(self, items: list[PreparedNews]) -> None:
        if not items:
            return
        try:
            async with async_session_factory() as session:
                known_sources = await _known_source_ids(session, items)
                survivors = _drop_orphans(items, known_sources)
                if not survivors:
                    return
                await session.execute(_summary_upsert(survivors))
                await session.commit()
        except STORE_ERRORS as error:
            raise NewsStoreError(f"summarized news write failed: items={len(items)}") from error

    async def list_unembedded(self, urls: list[str]) -> list[EventSummary]:
        if not urls:
            return []
        statement = _summary_select().where(
            News.url.in_(urls),
            News.event_cluster_id.is_(None),
            News.summary.is_not(None),
            News.event_extraction.is_not(None),
            News.summary_embedding.is_(None),
        )
        try:
            async with async_session_factory() as session:
                rows = (await session.execute(statement)).all()
        except STORE_ERRORS as error:
            raise NewsStoreError(f"unembedded news query failed: urls={len(urls)}") from error
        return [_to_summary(row) for row in rows]

    async def save_embeddings(self, summaries: list[EventSummary]) -> None:
        if not summaries:
            return
        statement = (
            update(cast(Table, News.__table__))
            .where(
                News.id == bindparam("embedding_news_id"),
                News.summary_embedding.is_(None),
            )
            .values(summary_embedding=bindparam("embedding_value"))
        )
        values = [
            {"embedding_news_id": summary.news_id, "embedding_value": list(summary.embedding)}
            for summary in summaries
        ]
        try:
            async with async_session_factory() as session:
                await session.execute(statement, values)
                await session.commit()
        except STORE_ERRORS as error:
            raise NewsStoreError(
                f"summary embedding write failed: items={len(summaries)}"
            ) from error

    async def list_pending(self, urls: list[str]) -> list[EventSummary]:
        if not urls:
            return []
        statement = _summary_select().where(
            News.url.in_(urls),
            News.event_cluster_id.is_(None),
            News.summary.is_not(None),
            News.event_extraction.is_not(None),
            News.summary_embedding.is_not(None),
        )
        try:
            async with async_session_factory() as session:
                rows = (await session.execute(statement)).all()
        except STORE_ERRORS as error:
            raise NewsStoreError(f"pending news query failed: urls={len(urls)}") from error
        return [_to_summary(row) for row in rows]

    async def find_candidates(self, query: CandidateQuery) -> list[CandidateCluster]:
        if not query.summary.embedding:
            return []
        try:
            async with async_session_factory() as session:
                scores = await _candidate_scores(session, query)
                anchors = await _candidate_anchors(session, [row.cluster_id for row in scores])
        except STORE_ERRORS as error:
            raise NewsStoreError(f"candidate query failed: id={query.summary.news_id}") from error
        return [
            CandidateCluster(row.cluster_id, float(row.score), tuple(anchors[row.cluster_id]))
            for row in scores
            if anchors[row.cluster_id]
        ]

    async def assign_clusters(self, assignments: list[ClusterAssignment]) -> None:
        if not assignments:
            return
        statement = (
            update(cast(Table, News.__table__))
            .where(
                News.id == bindparam("assignment_news_id"),
                News.event_cluster_id.is_(None),
            )
            .values(event_cluster_id=bindparam("assignment_cluster_id"))
        )
        values = [
            {
                "assignment_news_id": assignment.news_id,
                "assignment_cluster_id": assignment.cluster_id,
            }
            for assignment in assignments
        ]
        try:
            async with async_session_factory() as session:
                await session.execute(statement, values)
                await session.commit()
        except STORE_ERRORS as error:
            raise NewsStoreError(f"cluster assignment failed: items={len(assignments)}") from error


async def _known_source_ids(session: AsyncSession, items: list[PreparedNews]) -> set[uuid.UUID]:
    wanted = {item.news.source_id for item in items}
    rows = await session.execute(select(Source.id).where(Source.id.in_(wanted)))
    return set(rows.scalars().all())


def _drop_orphans(items: list[PreparedNews], known_sources: set[uuid.UUID]) -> list[PreparedNews]:
    """Skip items whose source is gone: `source_id` is NOT NULL, so a row needs its source
    to exist — a delete between the source check and this insert only costs one nack + requeue."""
    orphans = {item.news.source_id for item in items if item.news.source_id not in known_sources}
    if orphans:
        logger.warning(
            "news sources gone, items skipped: ids=%s items=%d",
            sorted(map(str, orphans)),
            sum(item.news.source_id in orphans for item in items),
        )
    return [item for item in items if item.news.source_id not in orphans]


def _summary_upsert(items: list[PreparedNews]):
    rows = [_prepared_row(item) for item in items]
    statement = postgres_insert(News).values(rows)
    incomplete = or_(
        News.summary.is_(None),
        News.event_extraction.is_(None),
    )
    return statement.on_conflict_do_update(
        index_elements=[News.url],
        set_={
            "summary": statement.excluded.summary,
            "event_extraction": statement.excluded.event_extraction,
            "summary_embedding": None,
            "event_cluster_id": None,
        },
        where=incomplete,
    )


def _prepared_row(item: PreparedNews) -> dict[str, object]:
    row = item.news.model_dump()
    row.update(
        {
            "id": item.summary.news_id,
            "summary": item.summary.text,
            "event_extraction": item.summary.extraction,
            "summary_embedding": None,
            "event_cluster_id": None,
        }
    )
    return row


def _summary_select():
    return select(
        News.id,
        News.url,
        News.summary,
        News.event_extraction,
        News.published_at,
        News.created_at,
        News.summary_embedding,
    )


def _to_summary(row) -> EventSummary:
    return EventSummary(
        news_id=row.id,
        url=row.url,
        text=row.summary,
        extraction=dict(row.event_extraction),
        published_at=row.published_at or row.created_at,
        embedding=tuple(row.summary_embedding or ()),
    )


async def _candidate_scores(session: AsyncSession, query: CandidateQuery):
    cluster_id = func.coalesce(News.event_cluster_id, News.id)
    similarity = literal(1.0) - News.summary_embedding.cosine_distance(
        list(query.summary.embedding)
    )
    best_score = func.max(similarity).label("score")
    reference_time = query.summary.published_at
    statement = select(cluster_id.label("cluster_id"), best_score).where(
        News.id != query.summary.news_id,
        News.summary_embedding.is_not(None),
        _is_available(query.available_pending_ids),
    )
    if reference_time is not None:
        window = timedelta(days=query.window_days)
        event_time = func.coalesce(News.published_at, News.created_at)
        statement = statement.where(
            event_time.between(reference_time - window, reference_time + window)
        )
    statement = (
        statement.group_by(cluster_id)
        .having(func.max(similarity) >= query.minimum_score)
        .order_by(desc("score"))
        .limit(query.limit)
    )
    return (await session.execute(statement)).all()


def _is_available(pending_ids: tuple[uuid.UUID, ...]):
    if not pending_ids:
        return News.event_cluster_id.is_not(None)
    return or_(News.event_cluster_id.is_not(None), News.id.in_(pending_ids))


async def _candidate_anchors(
    session: AsyncSession, cluster_ids: list[uuid.UUID]
) -> defaultdict[uuid.UUID, list[EventSummary]]:
    anchors: defaultdict[uuid.UUID, list[EventSummary]] = defaultdict(list)
    if not cluster_ids:
        return anchors
    rows = (await session.execute(_anchor_statement(cluster_ids))).all()
    for row in rows:
        anchors[row.cluster_id].append(_to_summary(row))
    return anchors


def _anchor_statement(cluster_ids: list[uuid.UUID]):
    cluster_id = func.coalesce(News.event_cluster_id, News.id).label("cluster_id")
    event_time = func.coalesce(News.published_at, News.created_at)
    base = select(
        cluster_id,
        News.id,
        News.url,
        News.summary,
        News.event_extraction,
        News.published_at,
        News.created_at,
        News.summary_embedding,
        func.row_number()
        .over(partition_by=cluster_id, order_by=(event_time.asc(), News.id.asc()))
        .label("oldest_rank"),
        func.row_number()
        .over(partition_by=cluster_id, order_by=(event_time.desc(), News.id.desc()))
        .label("newest_rank"),
    ).where(
        func.coalesce(News.event_cluster_id, News.id).in_(cluster_ids),
        News.summary.is_not(None),
        News.event_extraction.is_not(None),
        News.summary_embedding.is_not(None),
    )
    ranked = base.subquery()
    return select(ranked).where(or_(ranked.c.oldest_rank == 1, ranked.c.newest_rank == 1))
