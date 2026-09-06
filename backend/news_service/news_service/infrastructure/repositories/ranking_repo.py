"""PostgreSQL persistence for one relevance result per deduplicated cluster."""

import uuid
from collections import defaultdict

from common.core.db import async_session_factory
from common.entities.source import SourceReliability
from common.schemas import News, NewsClusterRanking
from sqlalchemy import case, func, or_, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from news_service.application.errors import NewsStoreError
from news_service.application.ports import RankingRepository
from news_service.domain.ranking import ClusterRankingTarget, RankingResult

STORE_ERRORS = (SQLAlchemyError, OSError)
SOURCE_SCORE = case(
    (News.source_reliability == SourceReliability.HIGH, 3),
    (News.source_reliability == SourceReliability.MEDIUM, 2),
    else_=1,
)


class SqlRankingRepository(RankingRepository):
    async def list_clusters(self, urls: list[str]) -> list[ClusterRankingTarget]:
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
    statement = (
        select(News.event_cluster_id)
        .where(News.url.in_(urls), News.event_cluster_id.is_not(None))
        .distinct()
    )
    values = (await session.execute(statement)).scalars().all()
    return [cluster_id for cluster_id in values if cluster_id is not None]


def _cluster_anchor_statement(cluster_ids: list[uuid.UUID]):
    cluster_id = News.event_cluster_id.label("cluster_id")
    event_time = func.coalesce(News.published_at, News.created_at)
    base = select(
        cluster_id,
        News.summary,
        News.event_extraction,
        News.summary_embedding,
        News.published_at,
        News.created_at,
        func.count().over(partition_by=News.event_cluster_id).label("member_count"),
        func.max(SOURCE_SCORE).over(partition_by=News.event_cluster_id).label("source_score"),
        func.row_number()
        .over(partition_by=News.event_cluster_id, order_by=(event_time.asc(), News.id.asc()))
        .label("oldest_rank"),
        func.row_number()
        .over(partition_by=News.event_cluster_id, order_by=(event_time.desc(), News.id.desc()))
        .label("newest_rank"),
    ).where(
        News.event_cluster_id.in_(cluster_ids),
        News.summary.is_not(None),
        News.event_extraction.is_not(None),
        News.summary_embedding.is_not(None),
    )
    ranked = base.subquery()
    return (
        select(ranked)
        .where(or_(ranked.c.oldest_rank == 1, ranked.c.newest_rank == 1))
        .order_by(ranked.c.cluster_id, ranked.c.oldest_rank)
    )


def _to_targets(rows) -> list[ClusterRankingTarget]:
    grouped: defaultdict[uuid.UUID, list] = defaultdict(list)
    for row in rows:
        grouped[row.cluster_id].append(row)
    return [
        _to_target(cluster_id, grouped[cluster_id])
        for cluster_id in sorted(grouped, key=lambda value: value.int)
    ]


def _to_target(cluster_id: uuid.UUID, anchors: list) -> ClusterRankingTarget:
    newest = max(anchors, key=lambda row: row.published_at or row.created_at)
    return ClusterRankingTarget(
        cluster_id=cluster_id,
        summaries=tuple(row.summary for row in anchors),
        extractions=tuple(dict(row.event_extraction) for row in anchors),
        embeddings=tuple(tuple(row.summary_embedding) for row in anchors),
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
            "context_score": ranking.context_score,
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
            "context_score": statement.excluded.context_score,
            "member_count": statement.excluded.member_count,
            "details": statement.excluded.details,
            "ranked_at": func.now(),
        },
    )
