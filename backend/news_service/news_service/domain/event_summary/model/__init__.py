"""What `EventSummary` is made of during ingestion."""

from news_service.domain.event_summary.model.news_target import NewsTarget
from news_service.domain.event_summary.model.prepared_news import PreparedNews
from news_service.domain.event_summary.model.stored_news_state import StoredNewsState

__all__ = ["NewsTarget", "PreparedNews", "StoredNewsState"]
