"""What a downloaded article page says about itself."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ArticleContent(BaseModel, frozen=True):
    """Body text plus the page's own metadata; attached to an `Article` once fetched."""

    final_url: str  # after redirects
    canonical_url: str | None = None
    title: str | None = None
    text: str
    word_count: int
    description: str | None = None
    author: str | None = None
    section: str | None = None
    language: str | None = None
    image_url: str | None = None
    modified_at: datetime | None = None
    fetched_at: datetime
    # Provenance kept for audit: the crawler's and the HTML's raw metadata.
    metadata: dict[str, Any] = Field(default_factory=dict)
