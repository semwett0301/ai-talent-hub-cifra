"""HTTP adapters. Imports stay lazy so one optional crawler cannot block another."""

__all__ = ["Crawl4AiPageFetcher", "FeedparserFeedReader"]


def __getattr__(name: str):
    if name == "Crawl4AiPageFetcher":
        from source_service.infrastructure.crawlers.crawl4ai_fetcher import Crawl4AiPageFetcher

        return Crawl4AiPageFetcher
    if name == "FeedparserFeedReader":
        from source_service.infrastructure.crawlers.feedparser_reader import FeedparserFeedReader

        return FeedparserFeedReader
    raise AttributeError(name)
