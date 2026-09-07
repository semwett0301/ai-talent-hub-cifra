"""Ports `infrastructure/repositories` implements."""

from news_service.application.ports.repositories.dedup_repository import DedupRepository
from news_service.application.ports.repositories.news_repository import NewsRepository
from news_service.application.ports.repositories.ranking_repository import RankingRepository

__all__ = ["DedupRepository", "NewsRepository", "RankingRepository"]
