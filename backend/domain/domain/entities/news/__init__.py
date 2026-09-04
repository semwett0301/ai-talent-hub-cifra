"""News contract — message shape, source type, and routing for the `news` exchange."""

from domain.entities.news.dto import ROUTING_PREFIX, NewsDTO, SourceType, routing_key

__all__ = ["ROUTING_PREFIX", "NewsDTO", "SourceType", "routing_key"]
