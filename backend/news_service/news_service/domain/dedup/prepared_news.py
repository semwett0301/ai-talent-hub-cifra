"""A news message whose event summary and embedding are ready to persist."""

from dataclasses import dataclass

from common.entities.news import NewsDTO

from news_service.domain.dedup.event_summary import EventSummary


@dataclass(frozen=True, slots=True)
class PreparedNews:
    news: NewsDTO
    summary: EventSummary
