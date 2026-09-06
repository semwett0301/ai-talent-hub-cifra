"""One changed article explained in plain language."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArticleChange:
    article: str
    summary: str
    before: str
    after: str
