"""`CrawlRun` — what one site crawl did, for the single summary log line."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field

from source_service.application.parse import DateSource
from source_service.domain import Article, ArticleStatus


@dataclass
class CrawlRun:
    site: str
    hubs: int = 0
    candidates: int = 0
    fetched: int = 0
    stopped_early: bool = False
    statuses: Counter[str] = field(default_factory=Counter)
    rejections: Counter[str] = field(default_factory=Counter)
    llm_dated: int = 0

    def record(self, articles: Iterable[Article]) -> None:
        """Count final verdicts; call once per article, after judgement."""
        for article in articles:
            self.statuses[str(article.status)] += 1
            if article.rejection is not None:
                self.rejections[str(article.rejection)] += 1
            if article.publication and article.publication.source == DateSource.LLM:
                self.llm_dated += 1

    @property
    def accepted(self) -> int:
        return self.statuses[str(ArticleStatus.ACCEPTED)]
