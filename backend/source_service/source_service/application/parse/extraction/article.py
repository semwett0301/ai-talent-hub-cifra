"""Article extraction from an already-fetched page (HTML text in, main text + date out).

news-please is the parsing tool: a deterministic stack (newspaper4k + readability +
date heuristics, no LLM). Only `from_html` is used — `from_url` goes through its
`SimpleCrawler`, which parks results in a class-level dict, so concurrent calls
silently return nothing. Fetching is the caller's job (the `PageFetcher` port).
Blocking (lxml) — callers on the event loop run it via `asyncio.to_thread`.
"""

from dataclasses import dataclass
from datetime import datetime

from common.core.logging import get_logger
from newsplease import NewsPlease

logger = get_logger(__name__)


@dataclass(frozen=True)
class ExtractedArticle:
    title: str | None
    text: str
    published_at: datetime | None


def extract_article(html: str, url: str) -> ExtractedArticle | None:
    """The article's main text and metadata; `None` (never raises) when nothing usable came out."""
    # What escapes news-please is its extractor stack choking on odd HTML/dates.
    try:
        article = NewsPlease.from_html(html, url=url, fetch_images=False)
    except (ValueError, TypeError, AttributeError) as exc:
        logger.warning("article extraction failed: url=%s (%s)", url, exc)
        return None

    # `{}` (not None) comes back for an empty page. Not `isinstance(_, NewsArticle)`:
    # news-please loads that class under a bare `NewsArticle` module, so it never matches.
    if isinstance(article, dict) or not article.maintext:
        return None

    return ExtractedArticle(
        title=article.title, text=article.maintext, published_at=article.date_publish
    )
