"""source_service domain — the web-news entities and the pure rules about them.

Nothing here does I/O or knows about Crawl4AI, LLMs or the pipeline order. The shared
kernel (the top-level `common` package) holds what crosses service boundaries; this
package holds what only this service reasons about.
"""

from .article import (
    ARTICLE_SCORER,
    Article,
    ArticleContent,
    ArticleOrigin,
    ArticleStatus,
    BodyRequirement,
    FreshnessWindow,
    PublicationDate,
    RejectReason,
    article_score,
    is_article_like,
    merge_duplicates,
    select_candidates,
)
from .hub import HUB_SCORER, Hub, HubOrigin, hub_score, merge_hubs, rank_hubs, select_hubs
from .scoring import RuleScorer, Score, ScoreRule
from .site import Site

__all__ = [
    "ARTICLE_SCORER",
    "HUB_SCORER",
    "Article",
    "ArticleContent",
    "ArticleOrigin",
    "ArticleStatus",
    "BodyRequirement",
    "FreshnessWindow",
    "Hub",
    "HubOrigin",
    "PublicationDate",
    "RejectReason",
    "RuleScorer",
    "Score",
    "ScoreRule",
    "Site",
    "article_score",
    "hub_score",
    "is_article_like",
    "merge_duplicates",
    "merge_hubs",
    "rank_hubs",
    "select_candidates",
    "select_hubs",
]
