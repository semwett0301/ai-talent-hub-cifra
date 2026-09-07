"""Stable output categories for corporate news relevance."""

from enum import StrEnum


class RelevanceCategory(StrEnum):
    LOW = "низкая релевантность"
    RELEVANT = "релевантно"
    IMPORTANT = "важно"
    ATTENTION = "требует внимания"
