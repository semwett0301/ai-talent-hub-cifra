from __future__ import annotations

from datetime import datetime
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
    output_dir: str = "output"

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
    # Zero means no hard page cap; date probes can still stop a dated hub crawl.
    best_first_max_pages: int = 80
    # 0 means no artificial cap. Listing pagination is stopped by its dates.
    max_hubs_per_site: int = Field(default=0, ge=0)
    min_hub_score: float = 0.35
    date_probe_start_page: int = Field(default=80, ge=1)
    date_probe_interval_pages: int = Field(default=20, ge=1)
    stop_hub_on_out_of_scope_probe: bool = True

    # 0 means no artificial candidate cap. For listing pages candidates are
    # already chronologically bounded by the first reliably old card.
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
    # Maximum simultaneous page fetches inside Crawl4AI arun_many/deep crawl.
    # Keep this below the site's rate limit; 8-16 is usually a practical range.
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
    # Stop article fetching only after consecutive batches contain enough known
    # dates and every such date is older than the requested window. This is a
    # conservative optimisation, not a proof that later URLs cannot be recent.
    stop_on_out_of_scope_batches: bool = True
    out_of_scope_consecutive_batches: int = 2
    out_of_scope_min_resolved_dates_per_batch: int = 8

    browser_use_fallback: bool = False
    browser_fallback_trigger_candidates_below: int = 3
    browser_headless: bool = True
    browser_max_steps: int = 14
    browser_max_hubs: int = 8


class AppConfig(BaseModel):
    sites: list[SiteConfig]
    settings: RuntimeSettings = Field(default_factory=RuntimeSettings)


class HubCandidate(BaseModel):
    url: str
    score: float
    title: str | None = None
    source: Literal["adaptive", "best_first", "browser_use", "seed"]


class DiscoveryTrace(BaseModel):
    site: str
    seed_url: str
    adaptive_confidence: float | None = None
    adaptive_metrics: dict = Field(default_factory=dict)
    adaptive_urls: list[str] = Field(default_factory=list)
    hubs: list[HubCandidate] = Field(default_factory=list)
    candidate_count: int = 0
    browser_fallback_used: bool = False
    best_first_runs: list[dict] = Field(default_factory=list)
    listing_runs: list[dict] = Field(default_factory=list)
    listing_classifications: list[dict] = Field(default_factory=list)
    extraction: dict = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    article_text_strategy: dict = Field(default_factory=dict)


class ArticleCandidate(BaseModel):
    url: str
    source_hub: str | None = None
    title_hint: str | None = None
    score: float = 0.0
    origin: Literal["adaptive", "best_first", "link", "browser_use", "listing"] = "link"


class LLMDateExtraction(BaseModel):
    is_article: bool = Field(description="True only for one individual editorial/publication page, not a listing.")
    published_at: str | None = Field(
        default=None,
        description="Publication date/time of THIS page. Keep timezone if visible. Null if not reliably identifiable.",
    )
    date_text: str | None = Field(
        default=None,
        description="Exact/near-exact visible date phrase used as evidence, if present.",
    )
    evidence: str | None = Field(
        default=None,
        description="Short explanation of why this is the page publication date rather than a date mentioned in article body.",
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ListingPageClassification(BaseModel):
    """Small, auditable LLM decision made from a compact page snapshot."""
    is_listing: bool
    # For a non-listing page: whether its visible navigation/content plausibly
    # leads to editorial news listings one hop below it.
    may_contain_news_listings: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(max_length=500)
    # Index into the pagination options supplied to the model; null means that
    # this page does not have an ordered next page.
    next_page_index: int | None = Field(default=None, ge=0)


class ArticleRecord(BaseModel):
    url: str
    canonical_url: str | None = None
    source_site: str
    source_hub: str | None = None

    title: str
    published_at: datetime
    modified_at: datetime | None = None
    author: str | None = None
    section: str | None = None
    language: str | None = None
    description: str | None = None
    image_url: str | None = None

    text: str
    word_count: int
    fetched_at: datetime

    date_source: Literal[
        "json_ld",
        "open_graph",
        "meta",
        "time_element",
        "visible_dom",
        "crawl4ai_llm",
    ]
    date_confidence: float = Field(ge=0.0, le=1.0)
    date_evidence: str | None = None
    metadata: dict = Field(default_factory=dict)
