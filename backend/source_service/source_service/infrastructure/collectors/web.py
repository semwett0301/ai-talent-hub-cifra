"""Pull adapter for ordinary web sources."""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from domain.core.logging import get_logger
from domain.entities.news import NewsDTO
from domain.schemas import Source

from source_service.application.ports import NewsCrawler, PullCollector
from source_service.application.web_crawl.pipeline import NewsPipeline
from source_service.application.web_crawl.settings import AppConfig, RuntimeSettings, SiteConfig

from .web_mapper import to_news_dto

logger = get_logger(__name__)

CrawlerFactory = Callable[[], AbstractAsyncContextManager[NewsCrawler]]
PipelineFactory = Callable[[AppConfig, NewsCrawler], NewsPipeline]


class WebCrawlCollector(PullCollector):
    """Run the web-news use case and adapt its records to the service contract."""

    def __init__(
        self,
        runtime: RuntimeSettings,
        crawler_factory: CrawlerFactory,
        pipeline_factory: PipelineFactory = NewsPipeline,
    ) -> None:
        self._runtime = runtime
        self._crawler_factory = crawler_factory
        self._pipeline_factory = pipeline_factory

    async def fetch(self, source: Source) -> list[NewsDTO]:
        config = AppConfig(
            sites=[SiteConfig(url=source.link, name=source.name)],
            settings=self._runtime,
        )
        logger.info("web crawl started: source=%s", source.link)
        try:
            async with self._crawler_factory() as crawler:
                articles = await self._pipeline_factory(config, crawler).run()
        except Exception:
            logger.exception("web crawl failed: %s", source.link)
            return []

        items: list[NewsDTO] = []
        for article in articles:
            try:
                items.append(to_news_dto(source, article))
            except Exception:
                logger.exception(
                    "web article adaptation failed: source=%s url=%s",
                    source.link,
                    article.url,
                )
        logger.info("web crawl finished: source=%s items=%d", source.link, len(items))
        return items
