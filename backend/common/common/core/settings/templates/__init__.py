"""Settings templates — one group of related variables per module."""

from .app import AppSettings
from .base import SettingsTemplate
from .edge import EdgeSettings
from .llm import LlmSettings
from .news import NewsConsumerSettings
from .npa import NpaSettings
from .postgres import PostgresSettings
from .rabbit import RabbitSettings
from .sources import SourceSchedulerSettings
from .telegram import TelegramSettings
from .web_crawl import WebCrawlSettings

__all__ = [
    "AppSettings",
    "EdgeSettings",
    "LlmSettings",
    "NewsConsumerSettings",
    "NpaSettings",
    "PostgresSettings",
    "RabbitSettings",
    "SettingsTemplate",
    "SourceSchedulerSettings",
    "TelegramSettings",
    "WebCrawlSettings",
]
