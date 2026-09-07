"""Settings templates — one group of related variables per module."""

from .app import AppSettings
from .base import SettingsTemplate
from .edge import EdgeSettings
from .llm import LlmSettings
from .news import NewsConsumerSettings
from .news_dedup import NewsDedupSettings
from .news_ranking import NewsRankingSettings
from .npa import NpaSettings
from .postgres import PostgresSettings
from .rabbit import RabbitSettings
from .rss_discovery import RssDiscoverySettings
from .sources import SourceSchedulerSettings
from .telegram import TelegramSettings
from .web_crawl import WebCrawlSettings

__all__ = [
    "AppSettings",
    "EdgeSettings",
    "LlmSettings",
    "NewsConsumerSettings",
    "NewsDedupSettings",
    "NewsRankingSettings",
    "NpaSettings",
    "PostgresSettings",
    "RabbitSettings",
    "RssDiscoverySettings",
    "SettingsTemplate",
    "SourceSchedulerSettings",
    "TelegramSettings",
    "WebCrawlSettings",
]
