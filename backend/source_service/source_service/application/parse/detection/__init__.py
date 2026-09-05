"""Detection — recognise a link's kind before any crawling: Telegram, RSS feed."""

from .rss import RssFeedLink, find_rss_feed_link
from .telegram import is_telegram_link

__all__ = [
    "RssFeedLink",
    "find_rss_feed_link",
    "is_telegram_link",
]
