"""Collector implementations, imported lazily to isolate optional dependencies."""

__all__ = ["RssCollector", "TelegramCollector", "WebCrawlCollector"]


def __getattr__(name: str):
    if name == "RssCollector":
        from source_service.infrastructure.collectors.rss import RssCollector

        return RssCollector
    if name == "TelegramCollector":
        from source_service.infrastructure.collectors.telegram import TelegramCollector

        return TelegramCollector
    if name == "WebCrawlCollector":
        from source_service.infrastructure.collectors.web import WebCrawlCollector

        return WebCrawlCollector
    raise AttributeError(name)
