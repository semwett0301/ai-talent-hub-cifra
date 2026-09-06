"""`Settings` — every group of configuration, aggregated once and read as `settings.<group>`."""

from functools import lru_cache

from pydantic import BaseModel, Field

from .templates import (
    AppSettings,
    EdgeSettings,
    LlmSettings,
    NewsConsumerSettings,
    NpaSettings,
    PostgresSettings,
    RabbitSettings,
    RssDiscoverySettings,
    SourceSchedulerSettings,
    TelegramSettings,
    WebCrawlSettings,
)


class Settings(BaseModel):
    """The root is a plain model: each group reads the environment itself when built, so
    variable names stay flat and a group can also be instantiated on its own (tests)."""

    app: AppSettings = Field(default_factory=AppSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    rabbit: RabbitSettings = Field(default_factory=RabbitSettings)
    edge: EdgeSettings = Field(default_factory=EdgeSettings)
    sources: SourceSchedulerSettings = Field(default_factory=SourceSchedulerSettings)
    rss_discovery: RssDiscoverySettings = Field(default_factory=RssDiscoverySettings)
    news: NewsConsumerSettings = Field(default_factory=NewsConsumerSettings)
    npa: NpaSettings = Field(default_factory=NpaSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    web_crawl: WebCrawlSettings = Field(default_factory=WebCrawlSettings)
    llm: LlmSettings = Field(default_factory=LlmSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
