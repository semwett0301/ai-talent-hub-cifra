import uuid
from datetime import UTC, datetime

import pytest
from news_service.application.services.news_ranker import NewsRanker
from news_service.domain.ranking import (
    ClusterRankingTarget,
    CompanyProfile,
    Facet,
    ImpactAssessment,
    RankingResult,
)
from news_service.infrastructure.ranking import load_company_profile


def _target(
    document: str, embedding: tuple[float, float], source_score: int
) -> ClusterRankingTarget:
    return ClusterRankingTarget(
        cluster_id=uuid.uuid4(),
        summaries=(document,),
        extractions=({"primary_event_found": True},),
        embeddings=(embedding,),
        published_at=datetime(2026, 9, 6, tzinfo=UTC),
        source_score=source_score,
        member_count=2,
    )


def _impact(score: int, urgency: int) -> ImpactAssessment:
    return ImpactAssessment(
        score,
        "finance",
        0,
        "reputation",
        0,
        "technology",
        0,
        "competition",
        "breaking",
        "urgent",
        urgency,
        {"finance_score": score, "urgency_basis": "breaking"},
    )


class _Repository:
    def __init__(self, targets: list[ClusterRankingTarget]) -> None:
        self.targets = targets
        self.saved: list[RankingResult] = []

    async def list_clusters(self, urls):
        return self.targets

    async def save_rankings(self, rankings):
        self.saved = rankings


class _Models:
    def __init__(self, impacts: list[ImpactAssessment], reranker_scores: list[float]) -> None:
        self.impacts = impacts
        self.reranker_scores = reranker_scores

    async def assess(self, company, targets, evaluated_at):
        return self.impacts

    async def rerank(self, company, targets):
        return self.reranker_scores


class _Embedder:
    def embed(self, summaries):
        return [[1.0, 0.0] for _ in summaries]


def test_packaged_company_profile_is_available():
    profile = load_company_profile()

    assert profile.name == "GS Labs"
    assert profile.facets


@pytest.mark.asyncio
async def test_ranking_persists_one_result_per_cluster():
    important = _target("IPTV platform launch", (1.0, 0.0), 3)
    noise = _target("football match", (0.0, 1.0), 1)
    repository = _Repository([important, noise])
    company = CompanyProfile("GS Labs", "IPTV", (Facet("iptv", "IPTV platform"),))
    ranker = NewsRanker(
        repository,  # type: ignore[arg-type]
        _Models([_impact(3, 3), _impact(0, 0)], [0.9, 0.1]),  # type: ignore[arg-type]
        _Embedder(),  # type: ignore[arg-type]
        company,
    )

    await ranker.process(["https://news.test/1", "https://news.test/2"])

    assert [ranking.cluster_id for ranking in repository.saved] == [
        important.cluster_id,
        noise.cluster_id,
    ]
    assert repository.saved[0].member_count == 2
    assert repository.saved[0].relevance_score > repository.saved[1].relevance_score
