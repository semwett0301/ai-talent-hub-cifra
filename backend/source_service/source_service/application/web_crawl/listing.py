from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup

from .date_utils import parse_date
from .url_utils import article_score, normalize_url

DATE_RE = re.compile(
    r"(?:20\d{2}[-./]\d{1,2}[-./]\d{1,2}|\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?|"
    r"\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря))"
    r"(?:\s*(?:в|\|)?\s*\d{1,2}:\d{2})?",
    re.I,
)
NEXT_TEXT_RE = re.compile(r"^(?:next|далее|дальше|следующ|older|older posts|>)$", re.I)


@dataclass(frozen=True)
class ListingLink:
    url: str
    title: str
    published_at: datetime | None


def listing_identity(url: str) -> str:
    """Identity for discovery: pagination variants are one listing hub."""
    parsed = urlparse(normalize_url(url))
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query)
        if key.lower() not in {"page", "p", "paged", "offset"}
    ]
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode(query), ""))


def is_pagination_url(url: str) -> bool:
    return any(
        key.lower() in {"page", "p", "paged", "offset"} for key, _ in parse_qsl(urlparse(url).query)
    )


def _card_date(anchor, timezone: str):
    """Read a date from the smallest card-like ancestor, never from page-wide text."""
    for node in [anchor, *list(anchor.parents)[:5]]:
        if not getattr(node, "get_text", None):
            continue
        text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))[:500]
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


def listing_links(
    html: str, *, base_url: str, timezone: str, score_threshold: float
) -> list[ListingLink]:
    """Article links in their visual/source order, with card-level dates when present."""
    soup = BeautifulSoup(html or "", "html.parser")
    seen: set[str] = set()
    out: list[ListingLink] = []
    for anchor in soup.find_all("a", href=True):
        title = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True))
        url = normalize_url(str(anchor.get("href") or ""), base=base_url)
        if not url or url in seen or len(title) < 12:
            continue
        if article_score(url, title=title, context=title) < score_threshold:
            continue
        seen.add(url)
        out.append(ListingLink(url=url, title=title, published_at=_card_date(anchor, timezone)))
    return out


def next_listing_page(html: str, *, base_url: str) -> str | None:
    soup = BeautifulSoup(html or "", "html.parser")
    for anchor in soup.find_all("a", href=True):
        rel = " ".join(anchor.get("rel") or [])
        text = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True))
        if "next" not in rel.lower() and not NEXT_TEXT_RE.match(text):
            continue
        url = normalize_url(str(anchor.get("href") or ""), base=base_url)
        if url:
            return url
    return None


def listing_llm_snapshot(html: str, *, base_url: str) -> dict[str, object]:
    """Bounded, untrusted evidence for deciding whether a page is a listing."""
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup.select("script, style, noscript, svg, nav, footer, aside, form"):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    h1 = soup.find("h1")
    main = soup.select_one("main, [role='main'], article") or soup.body or soup
    page_text = re.sub(r"\s+", " ", main.get_text(" ", strip=True))[:1800]
    cards = []
    for anchor in soup.find_all("a", href=True):
        label = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True))
        href = normalize_url(str(anchor.get("href") or ""), base=base_url)
        if len(label) < 16 or not href:
            continue
        parent = next(iter(anchor.parents), None)
        context = re.sub(r"\s+", " ", parent.get_text(" ", strip=True))[:360] if parent else label
        cards.append({"title": label[:220], "url": href, "context": context})
        if len(cards) == 6:
            break
    pagination: list[dict[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = normalize_url(str(anchor.get("href") or ""), base=base_url)
        label = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True))
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
