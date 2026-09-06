"""`SourceSchedulerSettings` — how `source_service` polls pull sources."""

from .base import SettingsTemplate


class SourceSchedulerSettings(SettingsTemplate):
    # Used when a source row's own `poll_interval_seconds` is null.
    source_poll_interval_seconds: int = 300
    # How many of a site's feeds an RSS source keeps (the finder ranks them; every one is
    # polled on each pull, so this caps the per-pull fetch count).
    source_rss_feeds_limit: int = 10
