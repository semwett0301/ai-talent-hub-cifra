"""Parse — pure link/page recognition, used by `SourceService` to auto-detect a source's type."""

from source_service.application.parse.rss import RssFeedLink, find_rss_feed_link
from source_service.application.parse.telegram import is_telegram_link

__all__ = ["RssFeedLink", "find_rss_feed_link", "is_telegram_link"]
