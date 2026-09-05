"""`WebCrawl` — one site, start to finish: hubs → cards → fetch → date → judge → dedupe."""

from dataclasses import dataclass

from common.core.logging import get_logger
from common.schemas import Source

from source_service.application.dto.crawl_run import CrawlRun
from source_service.application.ports.source import SourceRepository
from source_service.domain import Article, ArticleStatus, Site, merge_duplicates

from .articles import ArticleHarvest, ArticleJudgement, DateResolution
from .hubs import HubDiscovery
from .listings import CardCollection

logger = get_logger(__name__)


@dataclass(frozen=True)
class CrawlStages:
    """The five services one site crawl is composed of — `WebCrawl`'s only argument besides
    the repository, wired once in `deps`."""

    hubs: HubDiscovery
    cards: CardCollection
    harvest: ArticleHarvest
    dates: DateResolution
    judgement: ArticleJudgement


class WebCrawl:
    """Holds no logic of its own beyond the order of the stages, the not-relevant verdict
    and the dedupe: every judgement and every threshold lives in a stage. Each stage takes
    the whole list and touches only the status that is its own."""

    def __init__(self, stages: CrawlStages, repo: SourceRepository) -> None:
        self.__stages = stages
        self.__repo = repo

    async def run(self, source: Source) -> list[Article]:
        """Accepted articles for this source, freshest first. Marks the source not
        relevant when the search finds no candidate at all — no listing found."""
        site = Site(url=source.link, name=source.name)
        stats = CrawlRun(site=site.label)

        hubs = await self.__stages.hubs.run(site)
        stats.hubs = len(hubs)

        candidates = await self.__stages.cards.run(hubs)
        stats.candidates = len(candidates)
        if not candidates:
            return await self.__mark_not_relevant(source)

        fetched = await self.__stages.harvest.run(candidates, stats)
        dated = await self.__stages.dates.run(fetched)
        judged = self.__stages.judgement.run(dated)

        stats.record(judged)
        accepted = merge_duplicates([a for a in judged if a.status is ArticleStatus.ACCEPTED])

        logger.info(
            "web crawl finished: site=%s hubs=%d candidates=%d fetched=%d accepted=%d "
            "llm_dated=%d stopped_early=%s rejected=%s",
            site.seed,
            stats.hubs,
            stats.candidates,
            stats.fetched,
            len(accepted),
            stats.llm_dated,
            stats.stopped_early,
            dict(stats.rejections),
        )

        return accepted

    async def __mark_not_relevant(self, source: Source) -> list[Article]:
        await self.__repo.update(source, {"is_relevant": False, "is_enabled": False})
        logger.info("source marked not relevant: id=%s link=%s", source.id, source.link)
        return []
