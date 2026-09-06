"""API representation of a plain-language per-article change."""

from pydantic import BaseModel


class ArticleChangeOut(BaseModel):
    article: str
    summary: str
    before: str
    after: str
