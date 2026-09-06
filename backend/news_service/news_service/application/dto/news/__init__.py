"""News DTOs — the application's request and response contract (one class per module)."""

from news_service.application.dto.news.out import NewsOut
from news_service.application.dto.news.query import NewsQuery, NewsVisibility

__all__ = ["NewsOut", "NewsQuery", "NewsVisibility"]
