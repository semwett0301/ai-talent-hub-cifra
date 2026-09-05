"""`StaleStreak` — how many batches in a row came back with nothing fresh in them."""

from common.core.settings import WebCrawlSettings

from source_service.domain import Article, ArticleStatus, FreshnessWindow


class StaleStreak:
    """Counts consecutive batches whose dates all fell before the window, and says when
    that is enough to stop. Fresh for every site crawl."""

    def __init__(self, settings: WebCrawlSettings) -> None:
        self.__window = FreshnessWindow(days=settings.days, timezone=settings.timezone)
        self.__settings = settings
        self.__length = 0

    @property
    def length(self) -> int:
        return self.__length

    def should_stop(self, fetched: list[Article]) -> bool:
        """Records this batch and answers whether the run has left the freshness window
        for good. Always `False` while the early stop is switched off."""
        self.__length = self.__length + 1 if self.__is_stale(fetched) else 0
        return (
            self.__settings.stop_on_out_of_scope_batches
            and self.__length >= self.__settings.out_of_scope_consecutive_batches
        )

    def __is_stale(self, fetched: list[Article]) -> bool:
        """Stale: enough dates were readable in the markup, and not one of them was fresh."""
        dates = [
            a.publication.value
            for a in fetched
            if a.status is ArticleStatus.DATED and a.publication is not None
        ]
        if len(dates) < self.__settings.out_of_scope_min_resolved_dates_per_batch:
            return False
        return all(self.__window.is_before(date) for date in dates)
