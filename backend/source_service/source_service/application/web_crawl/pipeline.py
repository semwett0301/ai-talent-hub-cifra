from __future__ import annotations

import logging

from source_service.application.ports.news_crawler import NewsCrawler

from .discovery import NewsDiscovery
from .extractor import ArticleExtractor
from .models import ArticleRecord
from .settings import AppConfig

logger = logging.getLogger(__name__)


class NewsPipeline:
    def __init__(self, config: AppConfig, client: NewsCrawler):
        self.config = config
        self.client = client
        self.discovery_traces: list = []

    async def run(self, only_site: str | None = None) -> list[ArticleRecord]:
        settings = self.config.settings
        selected = [
            s
            for s in self.config.sites
            if s.enabled and (only_site is None or (s.name or "") == only_site)
        ]
        all_articles: dict[str, ArticleRecord] = {}

        discovery = NewsDiscovery(self.client, settings)
        extractor = ArticleExtractor(self.client, settings)

        for site in selected:
            site_name = site.name or str(site.url)
            logger.info("[%s] Этап 1/3: ищу listing-страницы от главной", site_name)
            trace, candidates = await discovery.run(site)

            self.discovery_traces.append(trace)
            logger.info(
                "[%s] Discovery завершён: listing=%d candidates=%d",
                site_name,
                len(trace.hubs),
                len(candidates),
            )

            if candidates:
                trace.article_text_strategy = await self.client.calibrate_article_text(
                    candidates[0].url
                )
            extracted = await extractor.extract_many(candidates, site_name)
            trace.extraction = extractor.last_run_stats
            for article in extracted:
                key = article.canonical_url or article.url
                previous = all_articles.get(key)
                if previous is None or article.published_at > previous.published_at:
                    all_articles[key] = article
            logger.info("[%s] Извлечено свежих статей=%d", site_name, len(extracted))

        return sorted(all_articles.values(), key=lambda a: a.published_at, reverse=True)
