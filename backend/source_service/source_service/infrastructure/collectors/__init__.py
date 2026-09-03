"""Collector implementations of the application collector ports."""

from source_service.infrastructure.collectors.rss import RssCollector
from source_service.infrastructure.collectors.telegram import TelegramCollector
from source_service.infrastructure.collectors.web import WebCrawlCollector

__all__ = ["RssCollector", "TelegramCollector", "WebCrawlCollector"]
