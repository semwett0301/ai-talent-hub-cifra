"""Application services — the news feed (read/dismiss), the batch ingest use case, and
the escalation of an alert into a legislative act."""

from news_service.application.services.news_deduplicator import NewsDeduplicator
from news_service.application.services.news_feed import NewsFeed
from news_service.application.services.news_ingestor import NewsIngestor
from news_service.application.services.news_ranker import NewsRanker
from news_service.application.services.npa_escalation import NpaEscalation

__all__ = ["NewsDeduplicator", "NewsFeed", "NewsIngestor", "NewsRanker", "NpaEscalation"]
