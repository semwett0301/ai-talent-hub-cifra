"""Deduplication infrastructure implementations."""

from news_service.infrastructure.dedup.openrouter_event_models import OpenRouterEventModels
from news_service.infrastructure.dedup.openrouter_summary_embedder import (
    OpenRouterSummaryEmbedder,
)

__all__ = ["OpenRouterEventModels", "OpenRouterSummaryEmbedder"]
