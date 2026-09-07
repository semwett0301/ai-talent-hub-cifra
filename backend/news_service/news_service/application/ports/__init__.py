"""Ports — interfaces application depends on, implemented in infrastructure or application.

Grouped the same way `infrastructure/` is: `dedup/`, `ranking/`, `repositories/`,
`gateways/` — a port and its implementation share a folder name across the two trees.

Two contracts intentionally do **not** live here. `NewsPipelineStage` sits inside
`application/services/news_ingestor/` — it never crosses into infrastructure (both its
implementers, `NewsDeduplicator`/`NewsRanker`, are application-layer, nested under the
same `news_ingestor` package as its sole consumer), so it isn't a port in the
cross-layer sense; splitting it across two top-level directories would only scatter one
cohesive concept. There is also no news-specific batch-handler port — `NewsIngestor`
implements the shared `common.core.rabbit.BatchHandler[NewsDTO]` directly; narrowing it
added nothing beyond a duplicate docstring, and it had exactly one implementer, wired by
name in `deps.py`.
"""

from news_service.application.ports.dedup import EventModels, SummaryEmbedder
from news_service.application.ports.gateways import NpaGateway
from news_service.application.ports.ranking import RankingModels
from news_service.application.ports.repositories import (
    DedupRepository,
    NewsRepository,
    RankingRepository,
)

__all__ = [
    "DedupRepository",
    "EventModels",
    "NewsRepository",
    "NpaGateway",
    "RankingModels",
    "RankingRepository",
    "SummaryEmbedder",
]
