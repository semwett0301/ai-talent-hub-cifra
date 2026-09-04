"""CRUD use-cases over sources — orchestrates the repository port.

Every mutation reconciles the runtime through the injected `SourceRegistrar`:
create/update (re)register the source, delete unregisters it — so pull scheduling
and push subscriptions stay in sync without a restart. `create`/`update` also
auto-detect the source's `type` from its `link` (clients never send `type`).
"""

import uuid

from domain.core.logging import get_logger
from domain.entities.news import SourceType
from domain.schemas import Source

from source_service.application.dto.source import SourceCreate, SourceUpdate
from source_service.application.parse import find_rss_feed_link, is_telegram_link
from source_service.application.ports import PageFetcher, SourceRegistrar, SourceRepository

logger = get_logger(__name__)


class SourceService:
    def __init__(
        self, repo: SourceRepository, registrar: SourceRegistrar, page_fetcher: PageFetcher
    ) -> None:
        self._repo = repo
        self._registrar = registrar
        self._page_fetcher = page_fetcher

    async def list(self) -> list[Source]:
        return await self._repo.list_all()

    async def get(self, source_id: uuid.UUID) -> Source | None:
        return await self._repo.get(source_id)

    async def create(self, payload: SourceCreate) -> Source:
        source_type, link = await self.__detect_type(payload.link)
        data = payload.model_dump() | {"type": source_type, "link": link}

        source = await self._repo.create(data)
        logger.info("source created: id=%s type=%s link=%s", source.id, source.type, source.link)

        await self._registrar.register(source)
        return source

    async def update(self, source: Source, payload: SourceUpdate) -> Source:
        changes = payload.model_dump(exclude_unset=True)
        if "link" in changes:
            changes["type"], changes["link"] = await self.__detect_type(changes["link"])

        updated = await self._repo.update(source, changes)
        logger.info(
            "source updated: id=%s fields=%s link=%s", updated.id, sorted(changes), updated.link
        )

        await self._registrar.register(updated)
        return updated

    async def delete(self, source: Source) -> None:
        source_id, link = source.id, source.link

        await self._repo.delete(source)
        logger.info("source deleted: id=%s link=%s", source_id, link)

        await self._registrar.unregister(source)

    async def __detect_type(self, link: str) -> tuple[SourceType, str]:
        """Telegram link -> TELEGRAM, unchanged. Else crawl the page: an RSS feed
        link -> RSS with `link` rewritten to the feed URL; otherwise, or if the
        page can't be fetched, -> WEB with `link` unchanged."""
        if is_telegram_link(link):
            return SourceType.TELEGRAM, link

        page_content = await self._page_fetcher.fetch(link)
        if page_content is None:
            logger.info("source type detected: link=%s -> web (page unreachable)", link)
            return SourceType.WEB, link

        feed = find_rss_feed_link(page_content, link)
        if feed is not None:
            logger.info("source type detected: link=%s -> rss feed=%s", link, feed.url)
            return SourceType.RSS, feed.url

        logger.info("source type detected: link=%s -> web (no feed link)", link)
        return SourceType.WEB, link
