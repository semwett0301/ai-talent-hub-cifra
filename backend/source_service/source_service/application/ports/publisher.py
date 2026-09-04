"""Publisher port — the message-bus contract, implemented in infrastructure."""

from typing import Protocol

from domain.entities.news import NewsDTO


class NewsPublisher(Protocol):
    """Publishes collected news items to the bus; returns the count published."""

    async def publish_news(self, items: list[NewsDTO]) -> int: ...
