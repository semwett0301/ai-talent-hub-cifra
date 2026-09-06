"""`RssDiscoverySettings` — how far feed discovery looks for a site's RSS feeds."""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .base import SettingsTemplate


class RssDiscoverySettings(SettingsTemplate):
    """Knobs of the feedsearch crawl `SourceService` runs on a new address. Read as
    `RSS_DISCOVERY_<FIELD>`; robots.txt is ignored by default because news sites fence
    their feeds off behind it and the operator named the site explicitly."""

    model_config = SettingsConfigDict(env_prefix="RSS_DISCOVERY_")

    max_depth: int = Field(default=3, ge=0)
    timeout_seconds: float = Field(default=30.0, gt=0)
    respect_robots: bool = False
    # Also probe the usual feed paths (/feed, /rss.xml, ...) when the pages advertise none.
    try_well_known_paths: bool = True
