"""`ArticleHarvest` — download the candidate pages, batch by batch, and know when to stop."""

from collections.abc import Iterator

from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings

from source_service.application.dto.crawl_run import CrawlRun
from source_service.domain import Article

from .fetching import ArticleFetching
from .state import StaleStreak

logger = get_logger(__name__)


def _batches(items: list[Article], size: int) -> Iterator[list[Article]]:
    step = max(1, size)
    for offset in range(0, len(items), step):
        yield items[offset : offset + step]


class ArticleHarvest:
    """Turns candidate links into downloaded pages. Holds no verdict of its own: the only
    thing it decides is how far down the list it is still worth paying to go."""

    def __init__(self, fetching: ArticleFetching, settings: WebCrawlSettings) -> None:
        self.__fetching = fetching
        self.__settings = settings

    async def run(self, candidates: list[Article], stats: CrawlRun) -> list[Article]:
        """Everything downloaded, `DATED` | `FETCHED` | `REJECTED`. Batch by batch, so a run
        over an archive stops once the printed dates go stale — candidates are ordered by
        relevance, not by time, so a single old page never ends the run."""
        if not candidates:
            return []
        selector = await self.__fetching.choose_container(candidates[0].url)
        streak = StaleStreak(self.__settings)
        fetched: list[Article] = []

        for batch in _batches(candidates, self.__settings.article_batch_size):
            read = await self.__fetching.run(batch, selector)
            fetched += read
            stats.fetched += len(batch)

            if streak.should_stop(read):
                stats.stopped_early = True
                logger.info(
                    "article fetching stopped: site=%s old_batches=%d", stats.site, streak.length
                )
                break
        return fetched
