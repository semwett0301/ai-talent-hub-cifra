"""Rules that tell one publication from a section, and the default `Article` scorer.

They read only what discovery already knows — the URL, the link text, crawler
metadata of an already-visited page — so a link is scored before its page is fetched.
"""

from urllib.parse import urlparse

from source_service.domain.article.article import Article
from source_service.domain.scoring import RuleScorer, ScoreRule
from source_service.domain.scoring.terms import (
    DATE_IN_PATH_RE,
    LONG_SLUG_RE,
    NUMERIC_ID_RE,
    SECTION_OR_JUNK_TERMS,
)
from source_service.domain.urls import path_depth

# Path segments that name one publication rather than a section.
ARTICLE_PATH_TERMS = (
    "/news/",
    "/article/",
    "/articles/",
    "/story/",
    "/post/",
    "/press/",
    "/press-release/",
    "/publication/",
    "/publications/",
    "/blog/",
    "/novosti/",
    "/statya/",
    "/stati/",
    "/publikac",
)

MIN_HEADLINE_LENGTH = 20
MIN_LONG_HEADLINE_LENGTH = 30
ARTICLE_METADATA_MARKERS = ("article", "newsarticle")

ArticleScorer = RuleScorer[Article]


def _path(article: Article) -> str:
    return urlparse(article.url).path.lower()


def _has_junk_path(article: Article) -> bool:
    return any(term in _path(article) for term in SECTION_OR_JUNK_TERMS)


def _has_article_path(article: Article) -> bool:
    return any(term in _path(article) for term in ARTICLE_PATH_TERMS)


def _has_date_in_path(article: Article) -> bool:
    return DATE_IN_PATH_RE.search(article.url) is not None


def _has_numeric_id(article: Article) -> bool:
    return NUMERIC_ID_RE.search(_path(article)) is not None


def _has_long_slug(article: Article) -> bool:
    return LONG_SLUG_RE.search(_path(article)) is not None


def _is_nested(article: Article) -> bool:
    return path_depth(article.url) >= 2


def _is_deeply_nested(article: Article) -> bool:
    return path_depth(article.url) >= 3


def _has_headline(article: Article) -> bool:
    return len((article.title_hint or "").strip()) >= MIN_HEADLINE_LENGTH


def _has_long_headline(article: Article) -> bool:
    return len((article.title_hint or "").strip()) >= MIN_LONG_HEADLINE_LENGTH


def _has_article_metadata(article: Article) -> bool:
    values = article.metadata.values()
    text = " ".join(str(v) for v in values if isinstance(v, (str, int, float))).lower()
    return any(marker in text for marker in ARTICLE_METADATA_MARKERS)


ARTICLE_RULES: tuple[ScoreRule[Article], ...] = (
    ScoreRule("junk_path", -0.45, _has_junk_path),
    ScoreRule("article_path", 0.24, _has_article_path),
    # A date in the path is a strong article marker, but never a publication date.
    ScoreRule("date_in_path", 0.22, _has_date_in_path),
    ScoreRule("numeric_id", 0.18, _has_numeric_id),
    ScoreRule("long_slug", 0.16, _has_long_slug),
    ScoreRule("nested", 0.08, _is_nested),
    ScoreRule("deeply_nested", 0.05, _is_deeply_nested),
    ScoreRule("headline", 0.10, _has_headline),
    ScoreRule("long_headline", 0.04, _has_long_headline),
    ScoreRule("article_metadata", 0.18, _has_article_metadata),
)

ARTICLE_SCORER: ArticleScorer = RuleScorer(ARTICLE_RULES)
