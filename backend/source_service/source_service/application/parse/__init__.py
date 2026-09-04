"""Parse — pure text-in/structure-out logic: link/page recognition for `SourceService`'s type
auto-detection, and article extraction for the RSS collector."""

from source_service.application.parse.article import ExtractedArticle, extract_article
from source_service.application.parse.rss import RssFeedLink, find_rss_feed_link
from source_service.application.parse.telegram import is_telegram_link

__all__ = [
    "ExtractedArticle",
    "RssFeedLink",
    "extract_article",
    "find_rss_feed_link",
    "is_telegram_link",
]
