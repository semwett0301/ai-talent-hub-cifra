"""`SourceSchedulerSettings` — how `source_service` polls pull sources."""

from .base import SettingsTemplate


class SourceSchedulerSettings(SettingsTemplate):
    # Used when a source row's own `poll_interval_seconds` is null.
    source_poll_interval_seconds: int = 300
