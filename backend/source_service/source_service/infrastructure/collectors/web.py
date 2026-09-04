"""Crawl arbitrary web sources and adapt the crawler output to ``NewsDTO``.

The embedded news agent is responsible for browser crawling, link discovery,
HTML/JSON-LD parsing, and selective LLM fallbacks. This adapter intentionally
knows only the application port and the shared message contract.
"""

from collections.abc import Callable
from typing import Any

from domain.core.logging import get_logger
from domain.core.settings import Settings
from domain.core.settings import settings as application_settings
from domain.entities.news import NewsDTO, SourceType
from domain.schemas import Source

from source_service.application.ports import PullCollector
from source_service.infrastructure.crawling.news_agent.config import EnvSettings
from source_service.infrastructure.crawling.news_agent.models import (
    AppConfig,
    ArticleRecord,
    RuntimeSettings,
    SiteConfig,
)
from source_service.infrastructure.crawling.news_agent.pipeline import NewsPipeline

logger = get_logger(__name__)

PipelineFactory = Callable[[AppConfig, EnvSettings], NewsPipeline]


def _agent_environment(config: Settings) -> EnvSettings:
    """Adapt the service's single settings object to the agent's LLM interface."""
    return EnvSettings(
        news_agent_model=config.news_agent_model,
        news_llm_provider=config.news_llm_provider,
        news_llm_api_token=config.news_llm_api_token,
        news_llm_base_url=config.news_llm_base_url,
        openrouter_api_key=config.openrouter_api_key,
        openrouter_base_url=config.openrouter_base_url,
        openrouter_model=config.openrouter_model,
        openai_api_key=config.openai_api_key,
        openai_base_url=config.openai_base_url,
    )


def _runtime_settings(config: Settings, env: EnvSettings) -> RuntimeSettings:
    """Set scheduler-safe limits and never try an LLM without credentials."""
    use_llm = config.web_crawl_llm_enabled and bool(env.llm_token())
    return RuntimeSettings(
        days=max(1, config.web_crawl_days),
        max_article_candidates_per_site=max(0, config.web_crawl_max_articles),
        llm_date_fallback=use_llm,
        listing_llm_max_calls_per_site=60 if use_llm else 0,
    )


class WebCrawlCollector(PullCollector):
    """``PullCollector`` implementation for sources detected as ordinary web pages.

    The full agent record is preserved under ``NewsDTO.raw['article']``. The
    exchange contract deliberately keeps only message-wide fields at top level;
    consumers that need title, canonical URL, author, dates or provenance can
    take them from ``raw`` without another fetch.
    """

    def __init__(
        self,
        config: Settings = application_settings,
        pipeline_factory: PipelineFactory = NewsPipeline,
    ) -> None:
        self._config = config
        self._pipeline_factory = pipeline_factory

    async def fetch(self, source: Source) -> list[NewsDTO]:
        env = _agent_environment(self._config)
        runtime = _runtime_settings(self._config, env)
        agent_config = AppConfig(
            sites=[SiteConfig(url=source.link, name=source.name)],
            settings=runtime,
        )

        logger.info(
            "web crawl started: source=%s days=%d max_articles=%d llm=%s",
            source.link,
            runtime.days,
            runtime.max_article_candidates_per_site,
            runtime.llm_date_fallback,
        )
        try:
            articles = await self._pipeline_factory(agent_config, env).run()
        except Exception:
            # A single inaccessible or malformed site must not take down the
            # scheduler's remaining source jobs.
            logger.exception("web crawl failed: %s", source.link)
            return []

        items: list[NewsDTO] = []
        for article in articles:
            try:
                items.append(self._to_news_dto(source, article))
            except Exception:
                # Retain successfully extracted neighbours if a site returns
                # one unexpected metadata value that cannot be serialised.
                logger.exception("web article adaptation failed: source=%s url=%s", source.link, article.url)
        logger.info("web crawl finished: source=%s items=%d", source.link, len(items))
        return items

    @staticmethod
    def _to_news_dto(source: Source, article: ArticleRecord) -> NewsDTO:
        article_payload = article.model_dump(mode="json")
        raw: dict[str, Any] = {
            # Convenient, stable access for consumers that do not need every
            # detail, plus an unmodified serializable agent result below.
            "title": article.title,
            "canonical_url": article.canonical_url,
            "author": article.author,
            "section": article.section,
            "language": article.language,
            "description": article.description,
            "image_url": article.image_url,
            "modified_at": article_payload["modified_at"],
            "fetched_at": article_payload["fetched_at"],
            "word_count": article.word_count,
            "date_source": article.date_source,
            "date_confidence": article.date_confidence,
            "date_evidence": article.date_evidence,
            "article": article_payload,
            "collector": {"name": "crawl4ai", "source_id": str(source.id)},
        }
        return NewsDTO(
            source_link=source.link,
            source_type=SourceType.WEB,
            source_reliability=source.reliability,
            url=article.url,
            text=article.text,
            published_at=article.published_at,
            raw=raw,
        )
