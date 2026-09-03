"""DTO/message contracts shared across services (producer + consumers)."""

from common.dto.news import NewsDTO
from common.dto.routing import ROUTING_PREFIX, routing_key

__all__ = ["NewsDTO", "ROUTING_PREFIX", "routing_key"]
