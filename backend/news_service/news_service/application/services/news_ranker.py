"""Cluster-level relevance ranking after event deduplication."""

from dataclasses import dataclass
from datetime import UTC, datetime

from common.core.logging import get_logger

from news_service.application.errors import RankingModelError
from news_service.application.ports import (
    NewsPipelineStage,
    RankingModels,
    RankingRepository,
    SummaryEmbedder,
)
from news_service.domain.ranking import (
    ClusterRankingTarget,
    CompanyProfile,
    ImpactAssessment,
    RankingResult,
)
from news_service.domain.ranking.rules import (
    calculate_bm25_component,
    calculate_bm25_scores,
    calculate_dense_context,
    calculate_relevance,
    categorize_relevance,
    combine_context,
)

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class _RankingSignals:
    bm25_score: float
    dense_score: float
    best_facet: str
    reranker_score: float


class NewsRanker(NewsPipelineStage):
    def __init__(
        self,
        repository: RankingRepository,
        models: RankingModels,
        embedder: SummaryEmbedder,
        company: CompanyProfile,
    ) -> None:
        self.__repository = repository
        self.__models = models
        self.__embedder = embedder
        self.__company = company
        self.__facet_vectors: list[list[float]] | None = None

    async def process(self, urls: list[str]) -> None:
        targets = await self.__repository.list_clusters(urls)
        if not targets:
            logger.info("news ranking skipped: reason=no_affected_clusters")
            return

        logger.info("news ranking started: clusters=%d", len(targets))
        impacts = await self.__models.assess(self.__company, targets, datetime.now(UTC))
        reranker_scores = await self.__models.rerank(self.__company, targets)
        _validate_counts(targets, impacts, reranker_scores)
        rankings = self.__build_rankings(targets, impacts, reranker_scores)
        await self.__repository.save_rankings(rankings)
        logger.info("news ranking completed: clusters=%d", len(rankings))

    def __build_rankings(
        self,
        targets: list[ClusterRankingTarget],
        impacts: list[ImpactAssessment],
        reranker_scores: list[float],
    ) -> list[RankingResult]:
        documents = [target.document for target in targets]
        bm25_scores = calculate_bm25_scores(self.__company.facets, documents)
        dense_rows = [self.__dense_context(target) for target in targets]
        return [
            _build_result(target, impact, _signals(values))
            for target, impact, values in zip(
                targets,
                impacts,
                zip(bm25_scores, dense_rows, reranker_scores, strict=True),
                strict=True,
            )
        ]

    def __dense_context(self, target: ClusterRankingTarget) -> tuple[float, str]:
        if self.__facet_vectors is None:
            queries = [facet.semantic_query for facet in self.__company.facets]
            self.__facet_vectors = self.__embedder.embed(queries)
        return calculate_dense_context(target, self.__company.facets, self.__facet_vectors)


def _validate_counts(
    targets: list[ClusterRankingTarget],
    impacts: list[ImpactAssessment],
    reranker_scores: list[float],
) -> None:
    if len(impacts) != len(targets):
        raise RankingModelError("impact assessment count does not match cluster count")
    if len(reranker_scores) != len(targets):
        raise RankingModelError("reranker score count does not match cluster count")


def _signals(values: tuple[float, tuple[float, str], float]) -> _RankingSignals:
    bm25_score, dense_row, reranker_score = values
    return _RankingSignals(bm25_score, *dense_row, reranker_score)


def _build_result(
    target: ClusterRankingTarget,
    impact: ImpactAssessment,
    signals: _RankingSignals,
) -> RankingResult:
    context = combine_context(signals.dense_score, signals.reranker_score)
    relevance = calculate_relevance(
        impact.impact_score, impact.urgency_score, target.source_score, signals.bm25_score
    )
    return RankingResult(
        cluster_id=target.cluster_id,
        relevance_score=relevance,
        category=categorize_relevance(relevance),
        context_score=context,
        member_count=target.member_count,
        details=_details(target, impact, signals, context),
    )


def _details(
    target: ClusterRankingTarget,
    impact: ImpactAssessment,
    signals: _RankingSignals,
    context: float,
) -> dict[str, object]:
    return {
        "components": {
            "impact": impact.impact_score,
            "urgency": impact.urgency_score,
            "source": target.source_score,
            "bm25": calculate_bm25_component(signals.bm25_score),
            "context": context,
        },
        "impact": impact.raw,
        "best_facet": signals.best_facet,
        "dense_score": signals.dense_score,
        "bm25_score": signals.bm25_score,
        "reranker_score": signals.reranker_score,
    }
