"""Duplicate articles: one story under several addresses is one record."""

from collections.abc import Iterable
from datetime import datetime

from source_service.domain.article.article import Article


def _published_at(article: Article) -> datetime:
    if article.publication is None:
        raise ValueError(f"only dated articles can be merged: {article.url}")
    return article.publication.value


def merge_duplicates(articles: Iterable[Article]) -> list[Article]:
    """Collapse articles that share an `identity`, keeping the one with the newer
    publication date, and return them newest first. Expects dated articles."""
    unique: dict[str, Article] = {}
    for article in articles:
        previous = unique.get(article.identity)
        if previous is None or _published_at(article) > _published_at(previous):
            unique[article.identity] = article
    return sorted(unique.values(), key=_published_at, reverse=True)
