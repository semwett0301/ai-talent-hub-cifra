"""External-model contract for impact assessment and semantic reranking."""

from datetime import datetime
from typing import Protocol

from news_service.domain.ranking import (
    ClusterRankingTarget,
    CompanyProfile,
    ImpactAssessment,
)


class RankingModels(Protocol):
    async def assess(
        self,
        company: CompanyProfile,
        targets: list[ClusterRankingTarget],
        evaluated_at: datetime,
    ) -> list[ImpactAssessment]: ...

    async def rerank(
        self, company: CompanyProfile, targets: list[ClusterRankingTarget]
    ) -> list[float]: ...
