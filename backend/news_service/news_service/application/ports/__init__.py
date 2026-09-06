"""Ports — interfaces application depends on, implemented in infrastructure or application."""

from news_service.application.ports.batch_handler import NewsBatchHandler
from news_service.application.ports.dedup_repository import DedupRepository
from news_service.application.ports.event_models import EventModels
from news_service.application.ports.npa_gateway import NpaGateway
from news_service.application.ports.pipeline_stage import NewsPipelineStage
from news_service.application.ports.ranking_models import RankingModels
from news_service.application.ports.ranking_repository import RankingRepository
from news_service.application.ports.repositories import NewsRepository
from news_service.application.ports.summary_embedder import SummaryEmbedder

__all__ = [
    "DedupRepository",
    "EventModels",
    "NewsBatchHandler",
    "NewsRepository",
    "NewsPipelineStage",
    "NpaGateway",
    "RankingModels",
    "RankingRepository",
    "SummaryEmbedder",
]
