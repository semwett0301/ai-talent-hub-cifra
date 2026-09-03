"""Source-related enums shared by the DTO contract and services."""

from enum import StrEnum


class SourceType(StrEnum):
    """How a source is collected."""

    TELEGRAM = "telegram"
    RSS = "rss"
    WEB = "web"
