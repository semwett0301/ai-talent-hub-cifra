"""`ArticleFetching` — DISCOVERED → DATED | FETCHED | REJECTED(FETCH_FAILED | TOO_SHORT)."""

from datetime import datetime
from zoneinfo import ZoneInfo

from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings

from source_service.application.parse import (
    article_body,
    choose_text_container,
    extract_html_metadata,
    extract_publication_date_signal,
    parse_date,
    word_count,
)
from source_service.application.ports.scraping import FetchedPage, PageCrawler
from source_service.domain import (
    Article,
    ArticleContent,
    ArticleStatus,
    BodyRequirement,
    PublicationDate,
    RejectReason,
)
from source_service.domain.urls import normalize_url

logger = get_logger(__name__)


def _clean(value: object) -> str | None:
    text = str(value).strip() if value else ""
    return text or None


class ArticleFetching:
    """Downloads one batch of candidate pages and reads them: body text, metadata and,
    while the HTML is still in hand, the machine-readable publication date. Raw HTML never
    leaves this service."""

    def __init__(self, crawler: PageCrawler, settings: WebCrawlSettings) -> None:
        self.__crawler = crawler
        self.__settings = settings
        self.__body = BodyRequirement(min_words=settings.min_article_words)

    async def choose_container(self, sample_url: str) -> str | None:
        """Once per site: which CSS container holds the article text on this site."""
        sample = await self.__crawler.crawl_page(sample_url)
        if sample is None:
            return None

        selector = choose_text_container(sample.html, self.__settings.min_article_words)
        logger.info(
            "text container calibrated: url=%s selector=%s", sample_url, selector or "document"
        )
        return selector

    async def run(self, articles: list[Article], selector: str | None) -> list[Article]:
        if not articles:
            return []
        pages = {
            page.url: page
            for page in await self.__crawler.crawl_articles([a.url for a in articles])
        }

        read = [self.__read(article, pages.get(article.url), selector) for article in articles]
        logger.info(
            "articles fetched: requested=%d ok=%d dated_from_markup=%d",
            len(articles),
            len(pages),
            sum(1 for a in read if a.status is ArticleStatus.DATED),
        )
        return read

    def __read(self, article: Article, page: FetchedPage | None, selector: str | None) -> Article:
        if page is None:
            return article.reject(RejectReason.FETCH_FAILED)

        body = article_body(page.html, page.markdown, selector, self.__settings.min_article_words)
        words = word_count(body)
        if not self.__body.accepts(words):
            return article.reject(RejectReason.TOO_SHORT)

        fetched = article.with_content(self.__content(article, page, body, words))
        return self.__date_from_markup(fetched, page.html)

    def __content(
        self, article: Article, page: FetchedPage, body: str, words: int
    ) -> ArticleContent:
        timezone = self.__settings.timezone
        html_meta = extract_html_metadata(page.html)
        crawler_meta = page.metadata
        final_url = normalize_url(page.final_url) or article.url

        canonical = html_meta.get("canonical_url")
        modified = html_meta.get("modified_at")

        return ArticleContent(
            final_url=final_url,
            canonical_url=(normalize_url(str(canonical), base=final_url) or None)
            if canonical
            else None,
            title=_clean(
                html_meta.get("title") or crawler_meta.get("title") or crawler_meta.get("og:title")
            ),
            text=body,
            word_count=words,
            description=_clean(html_meta.get("description") or crawler_meta.get("description")),
            author=_clean(html_meta.get("author")),
            section=_clean(html_meta.get("section")),
            language=_clean(html_meta.get("language") or crawler_meta.get("language")),
            image_url=_clean(html_meta.get("image_url")),
            modified_at=parse_date(str(modified), timezone) if modified else None,
            fetched_at=datetime.now(ZoneInfo(timezone)),
            metadata={"crawler_metadata": crawler_meta, "html_metadata": html_meta},
        )

    def __date_from_markup(self, fetched: Article, html: str) -> Article:
        """JSON-LD → OpenGraph → meta → <time> → visible DOM; none of them = stays FETCHED."""
        signal = extract_publication_date_signal(html)
        value = parse_date(signal.value, self.__settings.timezone) if signal.value else None
        if value is None or signal.source is None:
            return fetched
        return fetched.with_publication(
            PublicationDate(
                value=value,
                source=signal.source,
                confidence=signal.confidence,
                evidence=signal.evidence,
            )
        )
