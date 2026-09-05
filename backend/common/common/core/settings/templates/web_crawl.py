"""`WebCrawlSettings` — every knob of the WEB-source crawl, `WEB_CRAWL_*` in the env."""

from typing import Literal

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .base import SettingsTemplate

MAX_ARTICLES_ENV = "WEB_CRAWL_MAX_ARTICLES"


class WebCrawlSettings(SettingsTemplate):
    """A source is scanned independently, hence these are global operational limits
    rather than fields on the `Source` row. Only the first block is meant to be set in
    `.env`; the rest are tuning defaults that *can* be overridden as `WEB_CRAWL_<FIELD>`."""

    model_config = SettingsConfigDict(env_prefix="WEB_CRAWL_")

    # ---- the operator-facing knobs (documented in .env.example / README) ----
    days: int = Field(default=3, ge=1)  # freshness window
    max_article_candidates_per_site: int = Field(
        default=50, ge=0, validation_alias=MAX_ARTICLES_ENV
    )
    llm_enabled: bool = True  # LLM paths run only when this is on *and* a token exists
    timezone: str = "Europe/Moscow"

    # ---- listing discovery (primary route) ----
    listing_discovery_max_depth: int = Field(default=3, ge=0, le=3)
    # One discovered page costs at most one `classify_listing` call, so this caps both.
    listing_max_pages_per_site: int = Field(default=60, ge=0)  # 0 = unlimited
    listing_max_pages_per_hub: int = Field(default=0, ge=0)
    listing_llm_concurrency: int = Field(default=70, ge=1)
    listing_llm_max_tokens: int = Field(default=800, ge=100)
    listing_llm_min_confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    candidate_score_threshold: float = 0.18
    # A hub-discovery child link scoring at or above this already looks like one
    # article, not a section — so it's not a candidate for being a listing page.
    hub_link_max_article_score: float = 0.35
    max_hubs_per_site: int = Field(default=0, ge=0)

    # ---- fetching ----
    article_batch_size: int = 10
    crawl_concurrency: int = 12
    page_timeout_ms: int = 45_000
    check_robots_txt: bool = True
    user_agent: str = "NewsResearchCrawler/0.3"
    pruning_threshold: float = 0.42
    pruning_min_words: int = 30
    min_article_words: int = 80

    # ---- publication date ----
    llm_date_fallback: bool = True
    llm_date_min_confidence: float = 0.65
    llm_date_concurrency: int = Field(default=70, ge=1)
    llm_date_input_format: Literal["fit_markdown", "markdown", "html"] = "fit_markdown"
    llm_date_chunk_token_threshold: int = 5000
    llm_temperature: float = 0.0
    require_publication_date: bool = True

    # ---- early stop ----
    stop_on_out_of_scope_batches: bool = True
    out_of_scope_consecutive_batches: int = 2
    out_of_scope_min_resolved_dates_per_batch: int = 5
