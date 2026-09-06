"""Deduplication infrastructure implementations."""

from news_service.infrastructure.dedup.openrouter_event_models import OpenRouterEventModels
from news_service.infrastructure.dedup.sentence_transformer_embedder import (
    SentenceTransformerSummaryEmbedder,
)

__all__ = ["OpenRouterEventModels", "SentenceTransformerSummaryEmbedder"]
