"""Relevance of a news item's event cluster, flattened from the persisted ranking row."""

from typing import Any

from common.schemas import NewsClusterRanking
from pydantic import BaseModel, ConfigDict, model_validator

from news_service.application.dto.news.impact_reason import IMPACT_DIMENSIONS, ImpactReasonOut
from news_service.domain.event_cluster import RelevanceCategory


def _impact_reasons(impact: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "dimension": dimension,
            "score": impact[f"{dimension}_score"],
            "reason": impact[f"{dimension}_reason"],
        }
        for dimension in IMPACT_DIMENSIONS
    ]


def _from_ranking(ranking: NewsClusterRanking) -> dict[str, Any]:
    impact = ranking.details["impact"]
    return {
        "score": ranking.relevance_score,
        "category": ranking.category,
        "member_count": ranking.member_count,
        "urgency_basis": impact["urgency_basis"],
        "urgency_reason": impact["urgency_reason"],
        "impact": _impact_reasons(impact),
    }


class NewsRelevanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # 0–100, the category's thresholds are the ranker's (`domain.event_cluster.rules.scoring`).
    score: float
    category: RelevanceCategory
    # How many stored items report this same event.
    member_count: int
    urgency_basis: str
    urgency_reason: str
    impact: list[ImpactReasonOut]

    @model_validator(mode="before")
    @classmethod
    def _flatten_ranking_row(cls, value: object) -> object:
        """`NewsOut` is built from the ORM row; its ranking arrives as `NewsClusterRanking`."""
        if isinstance(value, NewsClusterRanking):
            return _from_ranking(value)
        return value
