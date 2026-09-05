from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from common.core.settings import WebCrawlSettings
from source_service.application.ports.scraping import DateGuess
from source_service.application.services.web.articles import DateResolution
from source_service.domain import Article, ArticleContent, ArticleStatus, RejectReason

URL = "https://example.test/news/1"


def fetched() -> Article:
    content = ArticleContent(
        final_url=URL,
        title="T",
        text="body",
        word_count=100,
        fetched_at=datetime.now(ZoneInfo("UTC")),
    )
    return Article(url=URL).with_content(content)


class FakeLlm:
    def __init__(self, guess: DateGuess | None):
        self.guess = guess
        self.calls: list[str] = []

    async def classify_listing(self, url, snapshot):
        return None

    async def resolve_publication_date(self, url: str, text: str) -> DateGuess | None:
        self.calls.append(url)
        return self.guess


@pytest.mark.asyncio
async def test_confident_guess_dates_the_article_with_llm_source():
    llm = FakeLlm(DateGuess(is_article=True, published_at="3 сентября 2026", confidence=0.9))
    resolution = DateResolution(llm, WebCrawlSettings())

    [article] = await resolution.run([fetched()])

    assert article.status is ArticleStatus.DATED
    assert article.publication is not None
    assert article.publication.source == "crawl4ai_llm"
    assert llm.calls == [URL]


@pytest.mark.asyncio
async def test_low_confidence_and_non_article_are_rejected():
    weak = DateResolution(
        FakeLlm(DateGuess(is_article=True, published_at="2026-09-03", confidence=0.2)),
        WebCrawlSettings(),
    )
    listing = DateResolution(
        FakeLlm(DateGuess(is_article=False, confidence=0.9)), WebCrawlSettings()
    )

    [no_date] = await weak.run([fetched()])
    [not_article] = await listing.run([fetched()])

    assert no_date.rejection is RejectReason.NO_DATE
    assert not_article.rejection is RejectReason.NOT_ARTICLE


@pytest.mark.asyncio
async def test_without_resolver_everything_is_no_date_and_nothing_is_called():
    resolution = DateResolution(None, WebCrawlSettings())
    [article] = await resolution.run([fetched()])
    assert article.rejection is RejectReason.NO_DATE


@pytest.mark.asyncio
async def test_budget_caps_the_calls_per_crawl():
    llm = FakeLlm(DateGuess(is_article=True, published_at="2026-09-03", confidence=0.9))
    resolution = DateResolution(llm, WebCrawlSettings(max_article_candidates_per_site=1))

    results = await resolution.run([fetched(), fetched()])

    assert len(llm.calls) == 1
    assert sorted(str(a.status) for a in results) == ["dated", "rejected"]
