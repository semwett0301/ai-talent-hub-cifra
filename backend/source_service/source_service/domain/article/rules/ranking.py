"""Ranking articles by how article-like they are — shared by every discovery route."""

from source_service.domain.article.article import Article

from .scoring import ARTICLE_SCORER


def article_score(article: Article) -> float:
    return ARTICLE_SCORER.score(article).value


def is_article_like(article: Article, min_score: float) -> bool:
    """Does the link look enough like one publication to be worth fetching?"""
    return article_score(article) >= min_score
