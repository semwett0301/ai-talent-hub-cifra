"""Scraping services — how to reach a site's publications: hubs, cards, fallback, fetching."""

from .article_fetching import ArticleFetching
from .card_collection import CardCollection
from .fallback_discovery import FallbackDiscovery
from .hub_discovery import HubDiscovery
from .web_crawl import WebCrawl

__all__ = [
    "ArticleFetching",
    "CardCollection",
    "FallbackDiscovery",
    "HubDiscovery",
    "WebCrawl",
]
