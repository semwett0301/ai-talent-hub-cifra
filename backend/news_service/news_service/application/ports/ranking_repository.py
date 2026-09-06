"""Persistence contract for cluster-level ranking checkpoints."""

from typing import Protocol

from news_service.domain.ranking import ClusterRankingTarget, RankingResult


class RankingRepository(Protocol):
    async def list_clusters(self, urls: list[str]) -> list[ClusterRankingTarget]: ...

    async def save_rankings(self, rankings: list[RankingResult]) -> None: ...
