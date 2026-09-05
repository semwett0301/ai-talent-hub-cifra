"""`ListingVerdict` — the LLM's answer to "is this page a list of publications?"."""

from pydantic import BaseModel, Field

MAX_RATIONALE_LENGTH = 500


class ListingVerdict(BaseModel):
    """Small, auditable decision made from a compact page snapshot."""

    is_listing: bool
    # For a non-listing page: does its navigation plausibly lead to listings one hop down?
    may_contain_news_listings: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(max_length=MAX_RATIONALE_LENGTH)
    # Index into the pagination options in the snapshot; null = no ordered next page.
    next_page_index: int | None = Field(default=None, ge=0)
