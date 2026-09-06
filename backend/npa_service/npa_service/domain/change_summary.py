"""Plain-language explanation of a transition between bill texts."""

from dataclasses import dataclass

from npa_service.domain.model import ArticleChange


@dataclass(frozen=True, slots=True)
class ChangeSummary:
    overall: str
    articles: tuple[ArticleChange, ...]
