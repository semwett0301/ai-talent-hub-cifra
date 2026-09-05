"""Browser crawler port — fetch pages with a real browser, hand back a plain shape."""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class PageLink:
    href: str
    text: str


@dataclass(frozen=True)
class FetchedPage:
    """A downloaded page, freed from the crawler library's own result type. The only
    form a page takes outside the adapter."""

    url: str  # as requested — the key callers match on
    final_url: str  # after redirects
    html: str
    markdown: str  # article-fit markdown from `crawl_articles`, raw markdown otherwise
    title: str | None
    links: tuple[PageLink, ...]  # internal links only
    metadata: dict[str, Any] = field(default_factory=dict)  # the crawler's page metadata


class PageCrawler(Protocol):
    """The browser. Never raises: a page that failed is simply absent from the result."""

    async def crawl_page(self, url: str) -> FetchedPage | None: ...

    async def crawl_pages(self, urls: list[str]) -> list[FetchedPage]: ...

    async def crawl_articles(self, urls: list[str]) -> list[FetchedPage]:
        """Like `crawl_pages`, but `markdown` is pruned to the article body."""
        ...
