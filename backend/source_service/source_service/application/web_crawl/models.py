from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HubCandidate(BaseModel):
    url: str
    score: float
    title: str | None = None
    source: Literal["adaptive", "best_first", "seed"]


class DiscoveryTrace(BaseModel):
    site: str
    seed_url: str
    adaptive_confidence: float | None = None
    adaptive_metrics: dict = Field(default_factory=dict)
    adaptive_urls: list[str] = Field(default_factory=list)
    hubs: list[HubCandidate] = Field(default_factory=list)
    candidate_count: int = 0
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
    origin: Literal["adaptive", "best_first", "link", "listing"] = "link"


class LLMDateExtraction(BaseModel):
    is_article: bool = Field(
        description="True only for one individual editorial/publication page, not a listing."
    )
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
