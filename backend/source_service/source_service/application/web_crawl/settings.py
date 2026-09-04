"""Configuration models for the web-crawl use case."""

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class SiteConfig(BaseModel):
    url: HttpUrl
    name: str | None = None
    enabled: bool = True
    allowed_domains: list[str] = Field(default_factory=list)


class RuntimeSettings(BaseModel):
    days: int = 3
    timezone: str = "Europe/Moscow"
    discovery_query: str = (
        "recent news press releases newsroom media publications articles company updates "
        "новости пресс-центр публикации статьи последние новости"
    )
    adaptive_enabled: bool = True
    adaptive_strategy: Literal["statistical", "embedding", "llm"] = "statistical"
    adaptive_confidence_threshold: float = 0.72
    adaptive_max_depth: int = 4
    adaptive_max_pages: int = 30
    adaptive_top_k_links: int = 5
    adaptive_min_gain_threshold: float = 0.05
    best_first_fallback: bool = True
    best_first_depth: int = 2
    best_first_max_pages: int = 80
    max_hubs_per_site: int = Field(default=0, ge=0)
    min_hub_score: float = 0.35
    date_probe_start_page: int = Field(default=80, ge=1)
    date_probe_interval_pages: int = Field(default=20, ge=1)
    stop_hub_on_out_of_scope_probe: bool = True
    max_article_candidates_per_site: int = Field(default=0, ge=0)
    candidate_score_threshold: float = 0.18
    listing_discovery_max_depth: int = Field(default=2, ge=0, le=2)
    listing_discovery_max_pages: int = Field(default=0, ge=0)
    listing_max_pages_per_hub: int = Field(default=0, ge=0)
    listing_llm_max_calls_per_site: int = Field(default=60, ge=0)
    listing_llm_concurrency: int = Field(default=70, ge=1)
    listing_llm_max_tokens: int = Field(default=800, ge=100)
    listing_llm_min_confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    article_batch_size: int = 40
    crawl_concurrency: int = 12
    page_timeout_ms: int = 45_000
    check_robots_txt: bool = True
    user_agent: str = "NewsResearchCrawler/0.3"
    pruning_threshold: float = 0.42
    pruning_min_words: int = 30
    min_article_words: int = 80
    llm_date_fallback: bool = True
    llm_date_min_confidence: float = 0.65
    llm_date_max_calls_per_site: int = 80
    llm_date_concurrency: int = Field(default=70, ge=1)
    llm_date_input_format: Literal["fit_markdown", "markdown", "html"] = "fit_markdown"
    llm_date_chunk_token_threshold: int = 5000
    llm_temperature: float = 0.0
    require_publication_date: bool = True
    stop_on_out_of_scope_batches: bool = True
    out_of_scope_consecutive_batches: int = 2
    out_of_scope_min_resolved_dates_per_batch: int = 8


class AppConfig(BaseModel):
    sites: list[SiteConfig]
    settings: RuntimeSettings = Field(default_factory=RuntimeSettings)
