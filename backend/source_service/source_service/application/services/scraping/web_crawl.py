"""`WebCrawl` — one site, start to finish: hubs → cards → fetch → date → judge → dedupe."""

from collections.abc import Iterator
from dataclasses import dataclass

from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings
from common.schemas import Source

from source_service.application.dto.crawl_run import CrawlRun
from source_service.application.ports.source import SourceRepository
from source_service.application.services.article import (
    ArticleJudgement,
    DateResolution,
    LlmDateBudget,
)
from source_service.domain import Article, ArticleStatus, RejectReason, Site, merge_duplicates

from .article_fetching import ArticleFetching
from .card_collection import CardCollection
from .hub_discovery import HubDiscovery

logger = get_logger(__name__)


def _batches(items: list[Article], size: int) -> Iterator[list[Article]]:
    step = max(1, size)
    for offset in range(0, len(items), step):
        yield items[offset : offset + step]


@dataclass(frozen=True)
class CrawlStages:
    """The five services one site crawl is composed of — `WebCrawl`'s only argument besides
    settings, wired once in `deps`."""

    hubs: HubDiscovery
    cards: CardCollection
    fetching: ArticleFetching
    dates: DateResolution
    judgement: ArticleJudgement


class WebCrawl:
    """Holds no logic of its own beyond order, routing by status, the early stop and the
    dedupe; every judgement lives in a stage."""

    def __init__(
        self, stages: CrawlStages, settings: WebCrawlSettings, repo: SourceRepository
    ) -> None:
        self.__stages = stages
        self.__settings = settings
        self.__repo = repo

    async def run(self, source: Source) -> list[Article]:
        """Accepted articles for this source, freshest first. Marks the source not
        relevant when the search finds no candidate at all — no listing found."""
        site = Site(url=source.link, name=source.name)
        run = CrawlRun(site=site.label)
        hubs = await self.__stages.hubs.run(site)
        run.hubs = len(hubs)

        candidates = await self.__stages.cards.run(hubs)
        run.candidates = len(candidates)

        if not candidates:
            await self.__repo.update(source, {"is_relevant": False, "is_enabled": False})
            logger.info("source marked not relevant: id=%s link=%s", source.id, source.link)
            return []

        accepted = merge_duplicates(await self.__extract(candidates, run))
        logger.info(
            "web crawl finished: site=%s hubs=%d candidates=%d fetched=%d accepted=%d "
            "llm_dated=%d stopped_early=%s rejected=%s",
            site.seed,
            run.hubs,
            run.candidates,
            run.fetched,
            len(accepted),
            run.llm_dated,
            run.stopped_early,
            dict(run.rejections),
        )
        return accepted

    async def __extract(self, candidates: list[Article], run: CrawlRun) -> list[Article]:
        """Batch by batch, so a run over an archive can stop once the dates go stale.
        Candidates are ordered by relevance, not by time — never stop on a single old page."""
        if not candidates:
            return []
        selector = await self.__stages.fetching.choose_container(candidates[0].url)
        budget = self.__stages.dates.budget()
        accepted: list[Article] = []
        old_streak = 0

        for batch in _batches(candidates, self.__settings.article_batch_size):
            judged = await self.__process(batch, selector, budget)
            run.record(judged)
            run.fetched += len(batch)
            accepted += [a for a in judged if a.status is ArticleStatus.ACCEPTED]

            old_streak = old_streak + 1 if self.__only_old_dates(judged) else 0
            if (
                self.__settings.stop_on_out_of_scope_batches
                and old_streak >= self.__settings.out_of_scope_consecutive_batches
            ):
                run.stopped_early = True
                logger.info(
                    "article fetching stopped: site=%s old_batches=%d", run.site, old_streak
                )
                break
        return accepted

    async def __process(
        self, batch: list[Article], selector: str | None, budget: LlmDateBudget
    ) -> list[Article]:
        """Route by status: markup-dated pages go straight to judgement, undated ones ask
        the LLM first, rejected ones are carried through for the report."""
        fetched = await self.__stages.fetching.run(batch, selector)
        resolved = await self.__stages.dates.run(
            [a for a in fetched if a.status is ArticleStatus.FETCHED], budget
        )

        dated = [a for a in fetched + resolved if a.status is ArticleStatus.DATED]
        rejected = [a for a in fetched + resolved if a.status is ArticleStatus.REJECTED]
        return rejected + self.__stages.judgement.run(dated)

    def __only_old_dates(self, judged: list[Article]) -> bool:
        """A batch is "old" when enough dates resolved and none of them was fresh."""
        recent = sum(
            1
            for a in judged
            if a.status is ArticleStatus.ACCEPTED or a.rejection is RejectReason.NO_TITLE
        )
        old = sum(1 for a in judged if a.rejection is RejectReason.OUT_OF_WINDOW)
        threshold = self.__settings.out_of_scope_min_resolved_dates_per_batch
        return recent + old >= threshold and recent == 0
