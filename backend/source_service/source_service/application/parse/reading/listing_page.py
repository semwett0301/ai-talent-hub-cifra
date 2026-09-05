"""Pure HTML reading of a listing page: its cards, its next page, its LLM snapshot.

Text in, domain out: the cards come back as `DISCOVERED` articles."""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup

from source_service.domain import Article, ArticleOrigin, is_article_like
from source_service.domain.urls import is_pagination_url, normalize_url

from .dates import RU_MONTH_NAMES, parse_date
from .html_text import clean_text

DATE_RE = re.compile(
    r"(?:20\d{2}[-./]\d{1,2}[-./]\d{1,2}|\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?|"
    r"\d{1,2}\s+(?:" + "|".join(RU_MONTH_NAMES) + r"))"
    r"(?:\s*(?:в|\|)?\s*\d{1,2}:\d{2})?",
    re.I,
)
NEXT_TEXT_RE = re.compile(r"^(?:next|далее|дальше|следующ|older|older posts|>)$", re.I)


def _card_date(anchor, timezone: str) -> datetime | None:
    """Read a date from the smallest card-like ancestor, never from page-wide text."""
    for node in [anchor, *list(anchor.parents)[:5]]:
        if not getattr(node, "get_text", None):
            continue
        text = clean_text(node, 500)
        found = DATE_RE.search(text)
        if found:
            value = parse_date(found.group(0), timezone)
            if value is not None:
                return value
        time_tag = node.find("time")
        if time_tag:
            value = parse_date(
                str(time_tag.get("datetime") or time_tag.get_text(" ", strip=True)), timezone
            )
            if value is not None:
                return value
    return None


def listing_cards(
    html: str, *, base_url: str, timezone: str, score_threshold: float, hub_url: str | None = None
) -> list[Article]:
    """The page's cards as `DISCOVERED` articles, in visual/source order: the link text
    becomes `title_hint`, the date printed on the card `card_published_at`."""
    soup = BeautifulSoup(html or "", "html.parser")
    seen: set[str] = set()
    out: list[Article] = []
    for anchor in soup.find_all("a", href=True):
        title = clean_text(anchor)
        url = normalize_url(str(anchor.get("href") or ""), base=base_url)
        if not url or url in seen or len(title) < 12:
            continue
        article = Article(
            url=url,
            hub_url=hub_url,
            title_hint=title,
            origin=ArticleOrigin.LISTING,
            card_published_at=_card_date(anchor, timezone),
        )
        if not is_article_like(article, score_threshold):
            continue
        seen.add(url)
        out.append(article)
    return out


def next_listing_page(html: str, *, base_url: str) -> str | None:
    soup = BeautifulSoup(html or "", "html.parser")
    for anchor in soup.find_all("a", href=True):
        rel = " ".join(anchor.get("rel") or [])
        text = clean_text(anchor)
        if "next" not in rel.lower() and not NEXT_TEXT_RE.match(text):
            continue
        url = normalize_url(str(anchor.get("href") or ""), base=base_url)
        if url:
            return url
    return None


def pagination_link(snapshot: dict[str, object], index: int | None) -> str | None:
    """The `index`-th pagination option of a `listing_llm_snapshot`, if there is one."""
    pagination = snapshot.get("pagination")
    if index is None or not isinstance(pagination, list) or index >= len(pagination):
        return None
    return str(pagination[index]["url"])


def listing_llm_snapshot(html: str, *, base_url: str) -> dict[str, object]:
    """Bounded, untrusted evidence for deciding whether a page is a listing."""
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup.select("script, style, noscript, svg, nav, footer, aside, form"):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    h1 = soup.find("h1")
    main = soup.select_one("main, [role='main'], article") or soup.body or soup
    page_text = clean_text(main, 1800)
    cards = []
    for anchor in soup.find_all("a", href=True):
        label = clean_text(anchor)
        href = normalize_url(str(anchor.get("href") or ""), base=base_url)
        if len(label) < 16 or not href:
            continue
        parent = next(iter(anchor.parents), None)
        context = clean_text(parent, 360) if parent else label
        cards.append({"title": label[:220], "url": href, "context": context})
        if len(cards) == 6:
            break
    pagination: list[dict[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = normalize_url(str(anchor.get("href") or ""), base=base_url)
        label = clean_text(anchor)
        rel = " ".join(anchor.get("rel") or [])
        if not href or not (
            is_pagination_url(href) or "next" in rel.lower() or NEXT_TEXT_RE.match(label)
        ):
            continue
        if href not in [item["url"] for item in pagination]:
            pagination.append({"url": href, "label": label[:80]})
        if len(pagination) == 8:
            break
    return {
        "title": title[:300],
        "h1": h1.get_text(" ", strip=True)[:300] if h1 else "",
        "page_text": page_text,
        "cards": cards,
        "pagination": pagination,
    }
