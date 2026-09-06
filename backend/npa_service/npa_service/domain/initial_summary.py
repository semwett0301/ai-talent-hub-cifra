"""AI-generated essentials for the first available bill version."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InitialSummary:
    """A short human-readable bill name and its plain-language essence."""

    title: str
    summary: str
