"""Application services — the news feed (read/dismiss) and the batch ingest use case."""

from news_service.application.services.news_feed import NewsFeed
from news_service.application.services.news_ingestor import NewsIngestor

__all__ = ["NewsFeed", "NewsIngestor"]
