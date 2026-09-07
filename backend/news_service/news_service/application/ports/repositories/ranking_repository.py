"""Persistence contract for cluster-level ranking checkpoints."""

from typing import Protocol

from news_service.domain.event_cluster import EventCluster, RankingResult


class RankingRepository(Protocol):
    async def list_clusters(self, urls: list[str]) -> list[EventCluster]: ...

    async def save_rankings(self, rankings: list[RankingResult]) -> None: ...
