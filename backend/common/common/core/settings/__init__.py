"""Shared configuration — the `settings` singleton every service reads (never `os.environ`).

All settings live here, split into groups (`templates/`) and aggregated by `Settings`:
`settings.postgres.async_database_url`, `settings.web_crawl.days`, …
"""

from common.core.settings.settings import Settings, get_settings, settings
from common.core.settings.templates import (
    AppSettings,
    EdgeSettings,
    LlmSettings,
    NewsConsumerSettings,
    NpaSettings,
    PostgresSettings,
    RabbitSettings,
    RssDiscoverySettings,
    SettingsTemplate,
    SourceSchedulerSettings,
    TelegramSettings,
    WebCrawlSettings,
)

__all__ = [
    "AppSettings",
    "EdgeSettings",
    "LlmSettings",
    "NewsConsumerSettings",
    "NpaSettings",
    "PostgresSettings",
    "RabbitSettings",
    "RssDiscoverySettings",
    "Settings",
    "SettingsTemplate",
    "SourceSchedulerSettings",
    "TelegramSettings",
    "WebCrawlSettings",
    "get_settings",
    "settings",
]
