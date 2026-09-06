"""CRUD use-cases over sources — orchestrates the repository port.

Every mutation reconciles the runtime through the injected `SourceRegistry`:
create/update (re)register the source, delete unregisters it — so pull scheduling
and push subscriptions stay in sync without a restart. `create`/`update` also
auto-detect the source's `type` from its `link` (clients never send `type`), and
everything the address implies — feed, identity, schedule, relevance — is derived
from that answer rather than accepted from the client.
"""

import uuid
from dataclasses import dataclass

from common.core.logging import get_logger
from common.core.settings import SourceSchedulerSettings
from common.entities.news import SourceType
from common.schemas import Source

from source_service.application.dto.source import SourceCreate, SourceUpdate
from source_service.application.errors import SourceNotRelevantError
from source_service.application.parse import find_rss_feed_link, is_telegram_link
from source_service.application.ports.scraping import PageFetcher
from source_service.application.ports.source import SourceRepository
from source_service.domain.urls import source_identity

from .source_registry import SourceRegistry

logger = get_logger(__name__)


@dataclass(frozen=True)
class DetectedSource:
    """What an address turned out to be — the answer `__detect_type` gives."""

    type: SourceType
    link: str
    rss_link: str | None


def _is_new_address(source: Source, changes: dict) -> bool:
    """The edit form always sends `link`, and detection hits the network — so only an
    address that is genuinely different from the stored one pays for a re-detect."""
    link = changes.get("link")

    return link is not None and source_identity(link) != source.normalized_link


def _check_relevance(source: Source, changes: dict) -> None:
    """`is_relevant` isn't client-settable; a non-relevant source stays disabled."""
    is_relevant = changes.get("is_relevant", source.is_relevant)

    if changes.get("is_enabled", source.is_enabled) and not is_relevant:
        raise SourceNotRelevantError(source.link)


class SourceService:
    def __init__(
        self,
        repo: SourceRepository,
        registrar: SourceRegistry,
        page_fetcher: PageFetcher,
        settings: SourceSchedulerSettings,
    ) -> None:
        self._repo = repo
        self._registrar = registrar
        self._page_fetcher = page_fetcher
        self._settings = settings

    async def list(self) -> list[Source]:
        return await self._repo.list_all()

    async def get(self, source_id: uuid.UUID) -> Source | None:
        return await self._repo.get(source_id)

    async def create(self, payload: SourceCreate) -> Source:
        detected = await self.__detect_type(payload.link)
        data = payload.model_dump() | self.__address_fields(detected, None)

        source = await self._repo.create(data)
        logger.info(
            "source created: id=%s type=%s link=%s rss_link=%s interval=%s",
            source.id,
            source.type,
            source.link,
            source.rss_link,
            source.poll_interval_seconds,
        )

        await self._registrar.register(source)
        return source

    async def update(self, source: Source, payload: SourceUpdate) -> Source:
        changes = payload.model_dump(exclude_unset=True)

        if _is_new_address(source, changes):
            derived = await self.__derive_from_link(source, changes["link"])
            changes = derived | changes

        _check_relevance(source, changes)

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

    async def __derive_from_link(self, source: Source, link: str) -> dict:
        """A new address is not the one the crawler judged, so the verdict goes. Only a
        source that verdict had force-disabled comes back on: one the operator switched
        off stays off."""
        detected = await self.__detect_type(link)
        fields = self.__address_fields(detected, source.poll_interval_seconds)

        return fields if source.is_relevant else fields | {"is_enabled": True}

    def __address_fields(self, detected: DetectedSource, current_interval: int | None) -> dict:
        """Everything the address implies, so create and update stay in step. `is_relevant`
        resets: a different address is not the one the crawler judged."""
        return {
            "type": detected.type,
            "link": detected.link,
            "rss_link": detected.rss_link,
            "normalized_link": source_identity(detected.link),
            "poll_interval_seconds": self.__poll_interval(detected.type, current_interval),
            "is_relevant": True,
        }

    def __poll_interval(self, source_type: SourceType, current: int | None) -> int | None:
        """Push sources stream, so they have no schedule at all; a pull source keeps the
        interval it already had and otherwise starts on the configured default."""
        if source_type == SourceType.TELEGRAM:
            return None

        return current or self._settings.source_poll_interval_seconds

    async def __detect_type(self, link: str) -> DetectedSource:
        """Telegram link -> TELEGRAM, `link` unchanged. Else crawl the page: an RSS
        feed link -> RSS, `link` unchanged and the feed URL returned separately as
        `rss_link`; otherwise, or if the page can't be fetched, -> WEB, no feed."""
        if is_telegram_link(link):
            return DetectedSource(SourceType.TELEGRAM, link, None)

        page_content = await self._page_fetcher.fetch(link)
        if page_content is None:
            logger.info("source type detected: link=%s -> web (page unreachable)", link)
            return DetectedSource(SourceType.WEB, link, None)

        feed = find_rss_feed_link(page_content, link)
        if feed is not None:
            logger.info("source type detected: link=%s -> rss feed=%s", link, feed.url)
            return DetectedSource(SourceType.RSS, link, feed.url)

        logger.info("source type detected: link=%s -> web (no feed link)", link)
        return DetectedSource(SourceType.WEB, link, None)
