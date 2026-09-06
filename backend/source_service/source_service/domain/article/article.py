"""`Article` — one publication on a web source, from discovered link to published news."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from common.entities.news import NewsDTO
from common.schemas import Source
from pydantic import BaseModel, Field

from .model import ArticleContent, ArticleOrigin, ArticleStatus, PublicationDate, RejectReason


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
        """The cross-service message: what the page said about itself, flat."""
        title = self.title

        if self.status is not ArticleStatus.ACCEPTED or not self.content or not self.publication:
            raise ValueError(f"only an accepted article becomes news: {self.url}")

        if title is None:
            raise ValueError(f"only a titled article becomes news: {self.url}")

        return NewsDTO.for_source(
            source,
            url=self.content.final_url,
            title=title,
            text=self.content.text,
            excerpt=self.content.description,
            published_at=self.publication.value,
            updated_at=self.content.modified_at,
            source_tags=[self.content.section] if self.content.section else [],
        )
