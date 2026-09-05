"""LLM port — the two questions the web crawl asks a language model."""

from typing import Protocol

from .date_guess import DateGuess
from .listing_verdict import ListingVerdict


class CrawlLlm(Protocol):
    """One model, one client, two questions. Both return `None` when the model failed or
    answered garbage — the caller then treats the page as "not a listing" / "no date"."""

    async def classify_listing(
        self, url: str, snapshot: dict[str, object]
    ) -> ListingVerdict | None:
        """Is this page a list of publications? Decided from a compact snapshot."""
        ...

    async def resolve_publication_date(self, url: str, text: str) -> DateGuess | None:
        """Read the already-fetched article text for its publication date."""
        ...
