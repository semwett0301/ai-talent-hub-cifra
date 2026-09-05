"""The article aggregate: the entity at the root, its sub-models in `model/`, its rules in `rules/`."""

from .article import Article
from .model import ArticleContent, ArticleOrigin, ArticleStatus, PublicationDate, RejectReason
from .rules import (
    ARTICLE_RULES,
    ARTICLE_SCORER,
    ArticleScorer,
    BodyRequirement,
    FreshnessWindow,
    article_score,
    is_article_like,
    merge_duplicates,
)

__all__ = [
    "ARTICLE_RULES",
    "ARTICLE_SCORER",
    "Article",
    "ArticleContent",
    "ArticleOrigin",
    "ArticleScorer",
    "ArticleStatus",
    "BodyRequirement",
    "FreshnessWindow",
    "PublicationDate",
    "RejectReason",
    "article_score",
    "is_article_like",
    "merge_duplicates",
]
