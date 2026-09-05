"""Shared configuration — the `settings` singleton every service reads (never `os.environ`).

All settings live here, split into groups (`templates/`) and aggregated by `Settings`:
`settings.postgres.async_database_url`, `settings.web_crawl.days`, …
"""

from common.core.settings.settings import Settings, get_settings, settings
from common.core.settings.templates import (
    ENV_FILE,
    AppSettings,
    EdgeSettings,
    LlmSettings,
    NewsConsumerSettings,
    PostgresSettings,
    RabbitSettings,
    SettingsTemplate,
    SourceSchedulerSettings,
    TelegramSettings,
    WebCrawlSettings,
)

__all__ = [
    "ENV_FILE",
    "AppSettings",
    "EdgeSettings",
    "LlmSettings",
    "NewsConsumerSettings",
    "PostgresSettings",
    "RabbitSettings",
    "Settings",
    "SettingsTemplate",
    "SourceSchedulerSettings",
    "TelegramSettings",
    "WebCrawlSettings",
    "get_settings",
    "settings",
]
