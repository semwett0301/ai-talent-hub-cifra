"""Cluster-level relevance ranking after event deduplication."""

from datetime import UTC, datetime

from common.core.logging import get_logger

from news_service.application.errors import RankingModelError
from news_service.application.ports import RankingModels, RankingRepository
from news_service.application.services.news_ingestor.pipeline_stage import NewsPipelineStage
from news_service.domain.company_profile import CompanyProfile
from news_service.domain.event_cluster import EventCluster, ImpactAssessment, RankingResult
from news_service.domain.event_cluster.rules import (
    calculate_bm25_component,
    calculate_bm25_scores,
    calculate_relevance,
    categorize_relevance,
)

logger = get_logger(__name__)


class NewsRanker(NewsPipelineStage):
    def __init__(
        self,
        repository: RankingRepository,
        models: RankingModels,
        company: CompanyProfile,
    ) -> None:
        self.__repository = repository
        self.__models = models
        self.__company = company

    async def process(self, urls: list[str]) -> None:
        targets = await self.__repository.list_clusters(urls)
        if not targets:
            logger.info("news ranking skipped: reason=no_affected_clusters")
            return

        logger.info("news ranking started: clusters=%d", len(targets))
        impacts = await self.__models.assess(self.__company, targets, datetime.now(UTC))
        _validate_counts(targets, impacts)
        rankings = self.__build_rankings(targets, impacts)
        await self.__repository.save_rankings(rankings)
        logger.info("news ranking completed: clusters=%d", len(rankings))

    def __build_rankings(
        self,
        targets: list[EventCluster],
        impacts: list[ImpactAssessment],
    ) -> list[RankingResult]:
        documents = [target.document for target in targets]
        bm25_scores = calculate_bm25_scores(self.__company.facets, documents)
        return [
            _build_result(target, impact, bm25_score)
            for target, impact, bm25_score in zip(targets, impacts, bm25_scores, strict=True)
        ]


def _validate_counts(targets: list[EventCluster], impacts: list[ImpactAssessment]) -> None:
    if len(impacts) != len(targets):
        raise RankingModelError("impact assessment count does not match cluster count")


def _build_result(
    target: EventCluster,
    impact: ImpactAssessment,
    bm25_score: float,
) -> RankingResult:
    relevance = calculate_relevance(
        impact.impact_score, impact.urgency_score, target.source_score, bm25_score
    )
    return RankingResult(
        cluster_id=target.cluster_id,
        relevance_score=relevance,
        category=categorize_relevance(relevance),
        member_count=target.member_count,
        details=_details(target, impact, bm25_score),
    )


def _details(
    target: EventCluster,
    impact: ImpactAssessment,
    bm25_score: float,
) -> dict[str, object]:
    return {
        "components": {
            "impact": impact.impact_score,
            "urgency": impact.urgency_score,
            "source": target.source_score,
            "bm25": calculate_bm25_component(bm25_score),
        },
        "impact": impact.raw,
        "bm25_score": bm25_score,
    }
