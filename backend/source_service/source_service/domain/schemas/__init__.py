"""Domain schemas — the service's data shapes.

`Source` is DB-backed (SQLAlchemy ORM); `NewsItem` is a plain in-memory shape
(collectors emit it, never stored). Same layer — they differ only in DB usage.
"""

from source_service.domain.schemas.news_item import NewsItem
from source_service.domain.schemas.source import Source

__all__ = ["NewsItem", "Source"]
