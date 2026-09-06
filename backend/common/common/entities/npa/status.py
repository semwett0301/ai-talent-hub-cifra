"""Lifecycle status for an NPA tracked on the State Duma website."""

from enum import StrEnum


class NpaTrackingStatus(StrEnum):
    """Whether the daily monitor should continue checking an act."""

    TRACKING = "tracking"
    PUBLISHED = "published"
    UNSUPPORTED = "unsupported"
