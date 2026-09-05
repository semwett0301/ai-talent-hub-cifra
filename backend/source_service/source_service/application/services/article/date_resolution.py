"""`DateResolution` — FETCHED → DATED | REJECTED(NO_DATE | NOT_ARTICLE), by asking the LLM."""

import asyncio

from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings

from source_service.application.parse import DateSource, parse_date
from source_service.application.ports.scraping import CrawlLlm, DateGuess
from source_service.domain import Article, ArticleStatus, PublicationDate, RejectReason

from .llm_date_budget import LlmDateBudget

logger = get_logger(__name__)


class DateResolution:
    """Only pages without a machine-readable date get here; the model reads the article
    text that is already in `content`. Without a resolver everything is `NO_DATE`."""

    def __init__(self, llm: CrawlLlm | None, settings: WebCrawlSettings):
        self.__llm = llm if settings.llm_date_fallback else None
        self.__settings = settings

    def budget(self) -> LlmDateBudget:
        """A fresh per-crawl budget; the orchestrator passes it to every `run` of one site."""
        return LlmDateBudget(
            max_calls=self.__settings.llm_date_max_calls_per_site,
            concurrency=self.__settings.llm_date_concurrency,
        )

    async def run(self, articles: list[Article], budget: LlmDateBudget) -> list[Article]:
        if not articles:
            return []
        if self.__llm is None:
            logger.info("llm date resolution skipped: articles=%d (no llm)", len(articles))
            return [article.reject(RejectReason.NO_DATE) for article in articles]

        resolved = list(await asyncio.gather(*(self.__resolve(a, budget) for a in articles)))
        logger.info(
            "dates resolved by llm: asked=%d dated=%d budget_left=%d",
            len(articles),
            sum(1 for a in resolved if a.status is ArticleStatus.DATED),
            budget.remaining,
        )
        return resolved

    async def __resolve(self, article: Article, budget: LlmDateBudget) -> Article:
        if article.status is not ArticleStatus.FETCHED or article.content is None:
            raise ValueError(f"date resolution expects a FETCHED article: {article.url}")

        guess, _ = await budget.run(lambda: self.__ask(article))
        if guess is None:
            return article.reject(RejectReason.NO_DATE)
        if not guess.is_article:
            return article.reject(RejectReason.NOT_ARTICLE)

        publication = self.__publication(guess)
        if publication is None:
            return article.reject(RejectReason.NO_DATE)
        return article.with_publication(publication)

    async def __ask(self, article: Article) -> DateGuess | None:
        assert self.__llm is not None and article.content is not None
        # Boundary with the model: a failed call is "no answer", never a crashed crawl.
        try:
            return await self.__llm.resolve_publication_date(article.url, article.content.text)
        except Exception:
            logger.exception("llm date resolution failed: url=%s", article.url)
            return None

    def __publication(self, guess: DateGuess) -> PublicationDate | None:
        if not guess.published_at or guess.confidence < self.__settings.llm_date_min_confidence:
            return None
        value = parse_date(guess.published_at, self.__settings.timezone)
        if value is None:
            return None
        return PublicationDate(
            value=value,
            source=DateSource.LLM,
            confidence=guess.confidence,
            evidence=guess.date_text or guess.evidence,
        )
