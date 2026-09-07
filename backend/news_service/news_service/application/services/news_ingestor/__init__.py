"""The batch ingestion pipeline: checkpointed summarization, then ordered stages."""

from news_service.application.services.news_ingestor.news_deduplicator import NewsDeduplicator
from news_service.application.services.news_ingestor.news_ingestor import NewsIngestor
from news_service.application.services.news_ingestor.news_ranker import NewsRanker
from news_service.application.services.news_ingestor.pipeline_stage import NewsPipelineStage

__all__ = ["NewsDeduplicator", "NewsIngestor", "NewsPipelineStage", "NewsRanker"]
