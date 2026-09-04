"""Port used by the web-news collection use case."""

from typing import Any, Protocol

from source_service.application.web_crawl.models import ListingPageClassification


class NewsCrawler(Protocol):
    article_css_selector: str | None

    async def adaptive_discover(self, seed_url: str) -> tuple[Any, float]: ...

    async def best_first_discover(self, url: str) -> tuple[list[Any], dict]: ...

    async def crawl_page(self, url: str) -> Any | None: ...

    async def crawl_pages(self, urls: list[str]) -> list[Any]: ...

    async def crawl_articles(self, urls: list[str]) -> list[Any]: ...

    async def calibrate_article_text(self, sample_url: str) -> dict[str, object]: ...

    async def classify_listing(
        self, *, url: str, snapshot: dict
    ) -> ListingPageClassification | None: ...

    async def extract_publication_date(self, url: str) -> Any | None: ...
