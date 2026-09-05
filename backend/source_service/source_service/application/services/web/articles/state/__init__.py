"""Per-run state of the article harvest — built inside `run`, never injected."""

from .stale_streak import StaleStreak

__all__ = ["StaleStreak"]
