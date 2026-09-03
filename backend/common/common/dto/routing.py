"""Routing helpers for the `news` exchange."""

from common.enums import SourceType

ROUTING_PREFIX = "news.raw"


def routing_key(source_type: SourceType) -> str:
    """`news.raw.telegram` / `news.raw.rss` / `news.raw.web`."""
    return f"{ROUTING_PREFIX}.{source_type.value}"
