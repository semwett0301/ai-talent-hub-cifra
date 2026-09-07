"""News DTOs — the application's request and response contract (one class per module)."""

from news_service.application.dto.news.impact_reason import ImpactReasonOut
from news_service.application.dto.news.out import NewsOut
from news_service.application.dto.news.query import NewsQuery, NewsVisibility
from news_service.application.dto.news.relevance import NewsRelevanceOut

__all__ = ["ImpactReasonOut", "NewsOut", "NewsQuery", "NewsRelevanceOut", "NewsVisibility"]
