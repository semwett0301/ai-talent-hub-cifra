"""Ranking articles by how article-like they are — shared by every discovery route."""

from collections.abc import Iterable

from source_service.domain.article.article import Article

from .scoring import ARTICLE_SCORER


def article_score(article: Article) -> float:
    return ARTICLE_SCORER.score(article).value


def is_article_like(article: Article, min_score: float) -> bool:
    """Does the link look enough like one publication to be worth fetching?"""
    return article_score(article) >= min_score


def select_candidates(articles: Iterable[Article], min_score: float) -> list[Article]:
    """Article-like candidates, one per URL (the better-scored sighting wins), best first."""
    best: dict[str, Article] = {}
    for article in articles:
        if not is_article_like(article, min_score):
            continue
        previous = best.get(article.url)
        if previous is None or article_score(article) > article_score(previous):
            best[article.url] = article
    return sorted(best.values(), key=article_score, reverse=True)
