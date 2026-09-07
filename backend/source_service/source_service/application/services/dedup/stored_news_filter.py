"""`StoredNewsFilter` — drop the entries a pull already has stored, before any page fetch."""

from typing import Protocol, TypeVar

from common.core.logging import get_logger

from source_service.application.ports.source import StoredNewsIndex

logger = get_logger(__name__)


class _UrlBearing(Protocol):
    @property
    def url(self) -> str: ...


ItemT = TypeVar("ItemT", bound=_UrlBearing)


class StoredNewsFilter:
    """Shared by every pull collector: what a source's poll found, minus what the shared
    `news` table already holds. `kind` only labels the log line (`"rss"`, `"web"`, ...)."""

    def __init__(self, stored_news: StoredNewsIndex, kind: str) -> None:
        self.__stored_news = stored_news
        self.__kind = kind

    async def unstored(self, source_link: str, items: list[ItemT]) -> list[ItemT]:
        if not items:
            return []

        stored = await self.__stored_news.list_stored_urls([item.url for item in items])
        fresh = [item for item in items if item.url not in stored]

        logger.info(
            "%s entries filtered: link=%s new=%d stored=%d",
            self.__kind,
            source_link,
            len(fresh),
            len(stored),
        )
        return fresh
