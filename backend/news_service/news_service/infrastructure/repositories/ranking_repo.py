"""PostgreSQL persistence for one relevance result per deduplicated cluster."""

import uuid
from collections import defaultdict
from typing import cast

from common.core.db import async_session_factory
from common.entities.source import SourceReliability
from common.schemas import News, NewsClusterRanking, NewsEventState
from sqlalchemy import case, func, or_, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from news_service.application.errors import NewsStoreError
from news_service.application.ports import RankingRepository
from news_service.domain.event_cluster import EventCluster, RankingResult

STORE_ERRORS = (SQLAlchemyError, OSError)
SOURCE_SCORE = case(
    (News.source_reliability == SourceReliability.HIGH, 3),
    (News.source_reliability == SourceReliability.MEDIUM, 2),
    else_=1,
)


class SqlRankingRepository(RankingRepository):
    async def list_clusters(self, urls: list[str]) -> list[EventCluster]:
        if not urls:
            return []
        try:
            async with async_session_factory() as session:
                cluster_ids = await _affected_cluster_ids(session, urls)
                if not cluster_ids:
                    return []
                rows = (await session.execute(_cluster_anchor_statement(cluster_ids))).all()
        except STORE_ERRORS as error:
            raise NewsStoreError(f"ranking cluster query failed: urls={len(urls)}") from error
        return _to_targets(rows)

    async def save_rankings(self, rankings: list[RankingResult]) -> None:
        if not rankings:
            return
        statement = _ranking_upsert(rankings)
        try:
            async with async_session_factory() as session:
                await session.execute(statement)
                await session.commit()
        except STORE_ERRORS as error:
            raise NewsStoreError(f"cluster ranking write failed: items={len(rankings)}") from error


async def _affected_cluster_ids(session: AsyncSession, urls: list[str]) -> list[uuid.UUID]:
    cluster_id = func.coalesce(NewsEventState.event_cluster_id, News.id)
    statement = (
        select(cluster_id)
        .select_from(News)
        .outerjoin(NewsEventState, NewsEventState.news_id == News.id)
        .where(News.url.in_(urls))
        .distinct()
    )
    values = (await session.execute(statement)).scalars().all()
    return cast(list[uuid.UUID], list(values))


def _cluster_anchor_statement(cluster_ids: list[uuid.UUID]):
    cluster_id = func.coalesce(NewsEventState.event_cluster_id, News.id).label("cluster_id")
    event_time = func.coalesce(News.published_at, News.created_at)
    base = (
        select(
            cluster_id,
            NewsEventState.summary,
            NewsEventState.primary_event_found,
            News.published_at,
            News.created_at,
            func.count().over(partition_by=cluster_id).label("member_count"),
            func.max(SOURCE_SCORE).over(partition_by=cluster_id).label("source_score"),
            func.row_number()
            .over(partition_by=cluster_id, order_by=(event_time.asc(), News.id.asc()))
            .label("oldest_rank"),
            func.row_number()
            .over(partition_by=cluster_id, order_by=(event_time.desc(), News.id.desc()))
            .label("newest_rank"),
        )
        .select_from(News)
        .join(NewsEventState, NewsEventState.news_id == News.id)
        .where(
            func.coalesce(NewsEventState.event_cluster_id, News.id).in_(cluster_ids),
            NewsEventState.summary.is_not(None),
            NewsEventState.primary_event_found.is_not(None),
            NewsEventState.summary_embedding.is_not(None),
        )
    )
    ranked = base.subquery()
    return (
        select(ranked)
        .where(or_(ranked.c.oldest_rank == 1, ranked.c.newest_rank == 1))
        .order_by(ranked.c.cluster_id, ranked.c.oldest_rank)
    )


def _to_targets(rows) -> list[EventCluster]:
    grouped: defaultdict[uuid.UUID, list] = defaultdict(list)
    for row in rows:
        grouped[row.cluster_id].append(row)
    return [
        _to_target(cluster_id, grouped[cluster_id])
        for cluster_id in sorted(grouped, key=lambda value: value.int)
    ]


def _to_target(cluster_id: uuid.UUID, anchors: list) -> EventCluster:
    newest = max(anchors, key=lambda row: row.published_at or row.created_at)
    return EventCluster(
        cluster_id=cluster_id,
        summaries=tuple(row.summary for row in anchors),
        primary_event_flags=tuple(row.primary_event_found for row in anchors),
        published_at=newest.published_at or newest.created_at,
        source_score=int(newest.source_score),
        member_count=int(newest.member_count),
    )


def _ranking_upsert(rankings: list[RankingResult]):
    rows = [
        {
            "cluster_id": ranking.cluster_id,
            "relevance_score": ranking.relevance_score,
            "category": ranking.category.value,
            "member_count": ranking.member_count,
            "details": ranking.details,
        }
        for ranking in rankings
    ]
    statement = postgres_insert(NewsClusterRanking).values(rows)
    return statement.on_conflict_do_update(
        index_elements=[NewsClusterRanking.cluster_id],
        set_={
            "relevance_score": statement.excluded.relevance_score,
            "category": statement.excluded.category,
            "member_count": statement.excluded.member_count,
            "details": statement.excluded.details,
            "ranked_at": func.now(),
        },
    )
