"""Ports `infrastructure/dedup` implements."""

from news_service.application.ports.dedup.event_models import EventModels
from news_service.application.ports.dedup.summary_embedder import SummaryEmbedder

__all__ = ["EventModels", "SummaryEmbedder"]
