"""External-model contract for cluster impact assessment."""

from datetime import datetime
from typing import Protocol

from news_service.domain.company_profile import CompanyProfile
from news_service.domain.event_cluster import EventCluster, ImpactAssessment


class RankingModels(Protocol):
    async def assess(
        self,
        company: CompanyProfile,
        targets: list[EventCluster],
        evaluated_at: datetime,
    ) -> list[ImpactAssessment]: ...
