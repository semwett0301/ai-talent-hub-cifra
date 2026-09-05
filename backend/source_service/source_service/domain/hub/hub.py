"""`Hub` — a page that lists publications: a news section, a press centre, a blog index."""

from pydantic import BaseModel

from source_service.domain.urls import listing_identity

from .model import HubOrigin

# Enough of a page's text to count the dated cards on it; never the whole document.
TEXT_EXCERPT_LIMIT = 9_000


class Hub(BaseModel, frozen=True):
    """A hub is never published itself; it is where article links are read from."""

    url: str
    origin: HubOrigin
    title: str | None = None
    text_excerpt: str = ""  # first `TEXT_EXCERPT_LIMIT` chars of the page, for scoring
    next_page: str | None = None  # the second listing page, when the classifier pointed at it

    @property
    def identity(self) -> str:
        """Pagination variants of one listing are one and the same hub."""
        return listing_identity(self.url)

    @classmethod
    def build(
        cls,
        url: str,
        origin: HubOrigin,
        title: str | None = None,
        text: str = "",
        next_page: str | None = None,
    ) -> "Hub":
        return cls(
            url=url,
            origin=origin,
            title=title or None,
            text_excerpt=text[:TEXT_EXCERPT_LIMIT],
            next_page=next_page,
        )
