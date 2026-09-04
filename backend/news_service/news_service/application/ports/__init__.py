"""Ports — interfaces application depends on, implemented in infrastructure."""

from news_service.application.ports.ingest import NewsBatchHandler
from news_service.application.ports.repositories import NewsRepository

__all__ = ["NewsBatchHandler", "NewsRepository"]
