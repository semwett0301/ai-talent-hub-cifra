"""Rules that tell a listing page from a single article, and the default `Hub` scorer.

Mirror image of the article rules: article markers (a date in the path, a numeric id,
a long slug) are penalties here — a hub is a section, not a story.
"""

import re
from urllib.parse import urlparse

from source_service.domain.hub.hub import Hub
from source_service.domain.scoring import RuleScorer, ScoreRule
from source_service.domain.scoring.terms import (
    DATE_IN_PATH_RE,
    LONG_SLUG_RE,
    NUMERIC_ID_RE,
    SECTION_OR_JUNK_TERMS,
)
from source_service.domain.urls import path_depth

# Words that name a section listing publications, in the URL or the title.
HUB_TERMS = (
    "news",
    "press",
    "press-center",
    "presscenter",
    "newsroom",
    "media",
    "blog",
    "article",
    "publication",
    "updates",
    "events",
    "новости",
    "пресс",
    "медиа",
    "публикац",
    "статьи",
    "события",
)
# A date as printed on a listing card.
DATE_LIKE_RE = re.compile(r"\b(?:20\d{2}|\d{1,2}[./-]\d{1,2}[./-]20\d{2})\b")

SHALLOW_DEPTH = 2
LONG_SLUG_MIN_DEPTH = 3
VERY_DEEP_DEPTH = 5
MIN_DATED_CARDS = 3

HubScorer = RuleScorer[Hub]


def _haystack(hub: Hub) -> str:
    return f"{hub.url} {hub.title or ''}".lower()


def _path(hub: Hub) -> str:
    return urlparse(hub.url).path.lower()


def _has_hub_terms(hub: Hub) -> bool:
    return any(term in _haystack(hub) for term in HUB_TERMS)


def _is_shallow(hub: Hub) -> bool:
    return path_depth(hub.url) <= SHALLOW_DEPTH


def _has_junk_terms(hub: Hub) -> bool:
    return any(term in _haystack(hub) for term in SECTION_OR_JUNK_TERMS)


def _has_date_in_path(hub: Hub) -> bool:
    return DATE_IN_PATH_RE.search(hub.url) is not None


def _has_numeric_id(hub: Hub) -> bool:
    return NUMERIC_ID_RE.search(_path(hub)) is not None


def _has_deep_long_slug(hub: Hub) -> bool:
    return (
        LONG_SLUG_RE.search(_path(hub)) is not None and path_depth(hub.url) >= LONG_SLUG_MIN_DEPTH
    )


def _is_very_deep(hub: Hub) -> bool:
    return path_depth(hub.url) >= VERY_DEEP_DEPTH


def _has_dated_cards(hub: Hub) -> bool:
    return len(DATE_LIKE_RE.findall(hub.text_excerpt)) >= MIN_DATED_CARDS


HUB_RULES: tuple[ScoreRule[Hub], ...] = (
    ScoreRule("hub_terms", 0.55, _has_hub_terms),
    ScoreRule("shallow", 0.12, _is_shallow),
    ScoreRule("junk_terms", -0.55, _has_junk_terms),
    # Strong article-shaped URLs should not become hubs merely for containing /news/.
    ScoreRule("date_in_path", -0.42, _has_date_in_path),
    ScoreRule("numeric_id", -0.30, _has_numeric_id),
    ScoreRule("deep_long_slug", -0.24, _has_deep_long_slug),
    ScoreRule("very_deep", -0.10, _is_very_deep),
    # Listing pages expose many dated cards; a weak but useful signal.
    ScoreRule("dated_cards", 0.16, _has_dated_cards),
)

HUB_SCORER: HubScorer = RuleScorer(HUB_RULES)
