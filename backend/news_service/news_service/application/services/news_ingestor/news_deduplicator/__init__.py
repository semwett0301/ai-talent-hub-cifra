"""The dedup stage of the ingestion pipeline."""

from news_service.application.services.news_ingestor.news_deduplicator.news_deduplicator import (
    NewsDeduplicator,
)

__all__ = ["NewsDeduplicator"]
