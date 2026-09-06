"""Settings templates — one group of related variables per module."""

from .app import AppSettings
from .base import ENV_FILE, SettingsTemplate
from .edge import EdgeSettings
from .llm import LlmSettings
from .news import NewsConsumerSettings
from .news_dedup import NewsDedupSettings
from .npa import NpaSettings
from .postgres import PostgresSettings
from .rabbit import RabbitSettings
from .sources import SourceSchedulerSettings
from .telegram import TelegramSettings
from .web_crawl import WebCrawlSettings

__all__ = [
    "ENV_FILE",
    "AppSettings",
    "EdgeSettings",
    "LlmSettings",
    "NewsConsumerSettings",
    "NewsDedupSettings",
    "NpaSettings",
    "PostgresSettings",
    "RabbitSettings",
    "SettingsTemplate",
    "SourceSchedulerSettings",
    "TelegramSettings",
    "WebCrawlSettings",
]
