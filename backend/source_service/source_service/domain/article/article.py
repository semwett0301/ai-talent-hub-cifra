"""`Article` — one publication on a web source, from discovered link to published news."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from common.entities.news import NewsDTO, SourceType
from common.schemas import Source
from pydantic import BaseModel, Field

from .model import ArticleContent, ArticleOrigin, ArticleStatus, PublicationDate, RejectReason

COLLECTOR_NAME = "crawl4ai"


class Article(BaseModel, frozen=True):
    """Immutable; every pipeline step returns a copy one stage further along.

    `content` appears at `FETCHED`, `publication` at `DATED`; `accept()` requires both,
    so an `ACCEPTED` article always has a title, a text and a trusted date.
    """

    url: str
    hub_url: str | None = None
    title_hint: str | None = None  # link text on the card that led here
    card_published_at: datetime | None = None  # the date printed on that card, if any
    origin: ArticleOrigin = ArticleOrigin.LINK
    # Crawler metadata known before the fetch (a page the discovery already visited).
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: ArticleStatus = ArticleStatus.DISCOVERED
    rejection: RejectReason | None = None
    content: ArticleContent | None = None
    publication: PublicationDate | None = None

    @property
    def identity(self) -> str:
        """What makes two records the same story: the declared canonical URL, else the
        final URL, else the link we started from."""
        if self.content is None:
            return self.url
        return self.content.canonical_url or self.content.final_url

    @property
    def title(self) -> str | None:
        page_title = self.content.title if self.content else None
        return page_title or self.title_hint

    def with_content(self, content: ArticleContent) -> Article:
        return self.model_copy(update={"content": content, "status": ArticleStatus.FETCHED})

    def with_publication(self, publication: PublicationDate) -> Article:
        return self.model_copy(update={"publication": publication, "status": ArticleStatus.DATED})

    def reject(self, reason: RejectReason) -> Article:
        return self.model_copy(update={"status": ArticleStatus.REJECTED, "rejection": reason})

    def accept(self) -> Article:
        if self.content is None or self.publication is None or not self.title:
            raise ValueError(f"cannot accept article without content, date and title: {self.url}")
        return self.model_copy(update={"status": ArticleStatus.ACCEPTED})

    def to_news_dto(self, source: Source) -> NewsDTO:
        """The cross-service message: compact fields plus the full record under `raw`."""
        if self.status is not ArticleStatus.ACCEPTED or not self.content or not self.publication:
            raise ValueError(f"only an accepted article becomes news: {self.url}")

        return NewsDTO.for_source(
            source.link,
            SourceType.WEB,
            source.reliability,
            url=self.content.final_url,
            text=self.content.text,
            published_at=self.publication.value,
            raw=self.__raw(source),
        )

    def __raw(self, source: Source) -> dict[str, Any]:
        assert self.content is not None and self.publication is not None
        payload = self.model_dump(mode="json")
        content = payload["content"]
        return {
            "title": self.title,
            "canonical_url": self.content.canonical_url,
            "author": self.content.author,
            "section": self.content.section,
            "language": self.content.language,
            "description": self.content.description,
            "image_url": self.content.image_url,
            "modified_at": content["modified_at"],
            "fetched_at": content["fetched_at"],
            "word_count": self.content.word_count,
            "date_source": self.publication.source,
            "date_confidence": self.publication.confidence,
            "date_evidence": self.publication.evidence,
            "article": payload,
            "collector": {"name": COLLECTOR_NAME, "source_id": str(source.id)},
        }
