"""Rules about an article: how article-like a link is, which dates count as fresh."""

from .body import BodyRequirement
from .duplicates import merge_duplicates
from .freshness import FreshnessWindow
from .ranking import article_score, is_article_like
from .scoring import ARTICLE_RULES, ARTICLE_SCORER, ArticleScorer

__all__ = [
    "ARTICLE_RULES",
    "ARTICLE_SCORER",
    "ArticleScorer",
    "BodyRequirement",
    "FreshnessWindow",
    "article_score",
    "is_article_like",
    "merge_duplicates",
]
