from __future__ import annotations

import logging

from .config import EnvSettings
from .crawl_client import Crawl4AIClient
from .discovery import NewsDiscovery
from .extractor import ArticleExtractor
from .models import AppConfig, ArticleRecord

logger = logging.getLogger(__name__)


class NewsPipeline:
    def __init__(self, config: AppConfig, env: EnvSettings):
        self.config = config
        self.env = env
        self.discovery_traces = []

    async def run(self, only_site: str | None = None) -> list[ArticleRecord]:
        settings = self.config.settings
        selected = [s for s in self.config.sites if s.enabled and (only_site is None or (s.name or "") == only_site)]
        all_articles: dict[str, ArticleRecord] = {}

        async with Crawl4AIClient(settings, self.env) as client:
            discovery = NewsDiscovery(client, settings)
            extractor = ArticleExtractor(client, settings)

            for site in selected:
                site_name = site.name or str(site.url)
                logger.info("[%s] Этап 1/3: ищу listing-страницы от главной (глубина ≤ 2)", site_name)
                trace, candidates = await discovery.run(site)

                self.discovery_traces.append(trace)
                logger.info(
                    "[%s] Этап 1/3 завершён: listing=%d, кандидатов статей=%d, adaptive_confidence=%s",
                    site_name,
                    len(trace.hubs),
                    len(candidates),
                    f"{trace.adaptive_confidence:.2f}" if trace.adaptive_confidence is not None else "n/a",
                )

                if candidates:
                    logger.info("[%s] Этап 2/3: подбираю стратегию очистки текста по первой статье", site_name)
                    trace.article_text_strategy = await client.calibrate_article_text(candidates[0].url)
                logger.info("[%s] Этап 3/3: извлекаю статьи и проверяю даты", site_name)
                extracted = await extractor.extract_many(candidates, site_name)
                trace.extraction = extractor.last_run_stats
                for article in extracted:
                    key = article.canonical_url or article.url
                    old = all_articles.get(key)
                    if old is None or article.published_at > old.published_at:
                        all_articles[key] = article
                logger.info("[%s] Готово: свежих статей=%d; статистика=%s", site_name, len(extracted), trace.extraction)

        return sorted(all_articles.values(), key=lambda a: a.published_at, reverse=True)
