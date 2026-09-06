"""CRUD use-cases over sources — orchestrates the repository port.

Every mutation reconciles the runtime through the injected `SourceRegistry`:
create/update (re)register the source, delete unregisters it — so pull scheduling
and push subscriptions stay in sync without a restart. `create`/`update` also
auto-detect the source's `type` from its `link` (clients never send `type`), and
everything the address implies — feeds, identity, schedule, relevance — is derived
from that answer rather than accepted from the client. A source and its feed URLs are
written together, one commit.
"""

import uuid
from dataclasses import dataclass

from common.core.logging import get_logger
from common.core.settings import SourceSchedulerSettings
from common.entities.news import SourceType
from common.schemas import Source

from source_service.application.dto.source import SourceCreate, SourceUpdate
from source_service.application.errors import SourceNotRelevantError
from source_service.application.parse import is_telegram_link
from source_service.application.ports.scraping import RssFeedFinder
from source_service.application.ports.source import SourceRepository
from source_service.domain.urls import source_identity

from .source_registry import SourceRegistry

logger = get_logger(__name__)


@dataclass(frozen=True)
class _DetectedSource:
    """What an address turned out to be — the answer `__detect_type` gives."""

    type: SourceType
    link: str
    rss_links: list[str]


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


def _keep_best_feeds(link: str, feed_urls: list[str], limit: int) -> list[str]:
    """The finder ranks feeds best-first; every kept feed is read on each pull, so the
    list is capped at the configured limit."""
    if len(feed_urls) <= limit:
        return feed_urls

    logger.info("rss feeds capped: link=%s found=%d kept=%d", link, len(feed_urls), limit)
    return feed_urls[:limit]


class SourceService:
    def __init__(
        self,
        repo: SourceRepository,
        registrar: SourceRegistry,
        feed_finder: RssFeedFinder,
        settings: SourceSchedulerSettings,
    ) -> None:
        self._repo = repo
        self._registrar = registrar
        self._feed_finder = feed_finder
        self._settings = settings

    async def list(self) -> list[Source]:
        return await self._repo.list_all()

    async def get(self, source_id: uuid.UUID) -> Source | None:
        return await self._repo.get(source_id)

    async def create(self, payload: SourceCreate) -> Source:
        detected = await self.__detect_type(payload.link)
        data = payload.model_dump() | self.__address_fields(detected, None)

        source = await self._repo.create(data, detected.rss_links)
        logger.info(
            "source created: id=%s type=%s link=%s feeds=%d interval=%s",
            source.id,
            source.type,
            source.link,
            len(detected.rss_links),
            source.poll_interval_seconds,
        )

        await self._registrar.register(source)
        return source

    async def update(self, source: Source, payload: SourceUpdate) -> Source:
        changes = payload.model_dump(exclude_unset=True)
        feed_urls: list[str] | None = None

        if _is_new_address(source, changes):
            detected = await self.__detect_type(changes["link"])

            changes = self.__derive_from_link(source, detected) | changes

            feed_urls = detected.rss_links
        elif "link" in changes:
            logger.info(
                "source re-detect skipped: id=%s link=%s (same address)", source.id, source.link
            )

        _check_relevance(source, changes)

        updated = await self._repo.update(source, changes, feed_urls)
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

    def __derive_from_link(self, source: Source, detected: _DetectedSource) -> dict:
        """A new address is not the one the crawler judged, so the verdict goes. Only a
        source that verdict had force-disabled comes back on: one the operator switched
        off stays off."""
        fields = self.__address_fields(detected, source.poll_interval_seconds)
        if source.is_relevant:
            return fields

        logger.info(
            "source relevance restored: id=%s link=%s (new address)", source.id, detected.link
        )
        return fields | {"is_enabled": True}

    def __address_fields(self, detected: _DetectedSource, current_interval: int | None) -> dict:
        """Everything the address implies, so create and update stay in step. `is_relevant`
        resets: a different address is not the one the crawler judged."""
        return {
            "type": detected.type,
            "link": detected.link,
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

    async def __detect_type(self, link: str) -> _DetectedSource:
        """Telegram link -> TELEGRAM, `link` unchanged. Else ask the feed finder: any
        RSS feed -> RSS, `link` unchanged and every feed URL kept as `rss_links`;
        none (or an unreachable site) -> WEB, no feeds."""
        if is_telegram_link(link):
            logger.info("source type detected: link=%s -> telegram (no fetch needed)", link)
            return _DetectedSource(SourceType.TELEGRAM, link, [])

        feed_urls = await self._feed_finder.find(link)
        if feed_urls:
            kept = _keep_best_feeds(link, feed_urls, self._settings.source_rss_feeds_limit)
            logger.info("source type detected: link=%s -> rss feeds=%d", link, len(kept))
            return _DetectedSource(SourceType.RSS, link, kept)

        logger.info("source type detected: link=%s -> web (no rss feeds)", link)
        return _DetectedSource(SourceType.WEB, link, [])
