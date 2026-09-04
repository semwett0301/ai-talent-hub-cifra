from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup

ARTICLE_TYPES = {"NewsArticle", "Article", "BlogPosting", "Report", "PressRelease", "TechArticle"}
DATE_TEXT_RE = re.compile(
    r"(?:\d{4}[-./]\d{1,2}[-./]\d{1,2}|\d{1,2}[-./]\d{1,2}[-./]\d{2,4}|"
    r"\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|"
    r"january|february|march|april|may|june|july|august|september|october|november|december))",
    re.I,
)
PUBLICATION_HINTS = ("publish", "publication", "posted", "created", "datepublished", "pubdate", "опублик")
DATE_HINTS = ("date", "time", "дата", "время")
ARTICLE_HINTS = ("article", "entry", "post", "story", "news", "header", "headline")
NON_PUBLICATION_HINTS = ("related", "recommend", "popular", "editor", "sidebar", "footer", "comment", "similar")


@dataclass
class PublicationDateSignal:
    value: str | None
    source: str | None
    confidence: float
    evidence: str | None = None


def _iter_jsonld(value: Any):
    if isinstance(value, dict):
        yield value
        graph = value.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from _iter_jsonld(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_jsonld(item)


def extract_html_metadata(html: str | None) -> dict:
    if not html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    out: dict[str, Any] = {}

    fields = {
        "title": ["og:title", "twitter:title"],
        "description": ["og:description", "description", "twitter:description"],
        "modified_at": ["article:modified_time", "dateModified", "last-modified"],
        "author": ["author", "article:author"],
        "section": ["article:section"],
        "language": ["og:locale", "language"],
        "image_url": ["og:image", "twitter:image"],
        "canonical_url": ["og:url"],
    }
    metas = soup.find_all("meta")
    for target, names in fields.items():
        for tag in metas:
            key = (tag.get("property") or tag.get("name") or tag.get("itemprop") or "").strip()
            if key in names and tag.get("content"):
                out[target] = str(tag.get("content")).strip()
                break

    canonical = soup.find("link", rel=lambda x: x and "canonical" in x)
    if canonical and canonical.get("href"):
        out["canonical_url"] = str(canonical.get("href")).strip()
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        out.setdefault("language", str(html_tag.get("lang")).strip())

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text("", strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        for item in _iter_jsonld(data):
            typ = item.get("@type")
            types = set(typ if isinstance(typ, list) else [typ])
            if not types.intersection(ARTICLE_TYPES):
                continue
            out.setdefault("schema_type", next(iter(types.intersection(ARTICLE_TYPES)), None))
            out.setdefault("title", item.get("headline") or item.get("name"))
            out.setdefault("description", item.get("description"))
            out.setdefault("jsonld_date_published", item.get("datePublished"))
            out.setdefault("modified_at", item.get("dateModified"))
            out.setdefault("section", item.get("articleSection"))
            out.setdefault("language", item.get("inLanguage"))
            image = item.get("image")
            if isinstance(image, str):
                out.setdefault("image_url", image)
            elif isinstance(image, dict):
                out.setdefault("image_url", image.get("url"))
            elif isinstance(image, list) and image:
                first = image[0]
                out.setdefault("image_url", first if isinstance(first, str) else first.get("url") if isinstance(first, dict) else None)
            author = item.get("author")
            if isinstance(author, dict):
                out.setdefault("author", author.get("name"))
            elif isinstance(author, list):
                names = [a.get("name") for a in author if isinstance(a, dict) and a.get("name")]
                if names:
                    out.setdefault("author", ", ".join(names))
            elif isinstance(author, str):
                out.setdefault("author", author)
            break
    return {k: v for k, v in out.items() if v not in (None, "", [])}


def _attribute_text(tag) -> str:
    values = [tag.name or ""]
    for key in ("class", "id", "itemprop", "data-testid", "data-test"):
        value = tag.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif value:
            values.append(str(value))
    return " ".join(values).lower()


def _visible_date_candidate(tag) -> tuple[int, str, str] | None:
    """Score a visible date only when its DOM context suggests publication."""
    text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True))[:200]
    if not DATE_TEXT_RE.search(text):
        return None

    own = _attribute_text(tag)
    ancestors = list(tag.parents)[:5]
    context = " ".join(_attribute_text(parent) for parent in ancestors)
    if any(hint in own or hint in context for hint in NON_PUBLICATION_HINTS):
        return None

    score = 0
    if tag.name == "time":
        score += 3
    if any(hint in own for hint in PUBLICATION_HINTS):
        score += 5
    elif any(hint in own for hint in DATE_HINTS):
        score += 3
    if any(hint in own or hint in context for hint in ARTICLE_HINTS):
        score += 2
    if any(getattr(parent, "name", None) == "article" for parent in ancestors):
        score += 2
    if any(hint in own or hint in context for hint in ("header", "headline")):
        score += 3
    # A date in the same compact DOM block as the page H1 is much more likely
    # to describe this publication than a date in an article card or sidebar.
    if any(parent.find("h1") is not None for parent in ancestors[:3]):
        score += 4
    if tag.find_previous("h1") is not None:
        score += 1

    if score < 6:
        return None
    evidence = f"<{tag.name} {own[:120]}>: {text}"
    return score, text, evidence


def extract_publication_date_signal(html: str | None) -> PublicationDateSignal:
    """Only high-confidence page-level date signals.

    We deliberately do not regex the whole article body: a random date mentioned in
    the story is not a publication date. If these signals are absent, the caller
    should use the LLM fallback.
    """
    if not html:
        return PublicationDateSignal(None, None, 0.0)
    soup = BeautifulSoup(html, "html.parser")

    # 1) JSON-LD datePublished on an Article-like entity.
    meta = extract_html_metadata(html)
    if meta.get("jsonld_date_published"):
        value = str(meta["jsonld_date_published"])
        return PublicationDateSignal(value, "json_ld", 0.99, f"JSON-LD datePublished={value}")

    # 2) OpenGraph article publication time.
    for tag in soup.find_all("meta"):
        key = (tag.get("property") or tag.get("name") or tag.get("itemprop") or "").strip()
        content = str(tag.get("content") or "").strip()
        if key == "article:published_time" and content:
            return PublicationDateSignal(content, "open_graph", 0.98, f"article:published_time={content}")

    # 3) Common machine-readable publication date meta/itemprop fields.
    reliable_keys = {
        "datePublished", "datepublished", "pubdate", "publish-date", "publishdate",
        "publication_date", "publication-date", "publish_date", "publish-date-time",
    }
    for tag in soup.find_all("meta"):
        key = (tag.get("property") or tag.get("name") or tag.get("itemprop") or "").strip()
        content = str(tag.get("content") or "").strip()
        if key in reliable_keys and content:
            return PublicationDateSignal(content, "meta", 0.93, f"meta[{key}]={content}")

    # 4) <time datetime=...> near the top of the article is usually reliable, but
    # slightly less universal than explicit publication metadata.
    for time_tag in soup.find_all("time", limit=8):
        value = str(time_tag.get("datetime") or "").strip()
        if value:
            text = re.sub(r"\s+", " ", time_tag.get_text(" ", strip=True))[:200]
            return PublicationDateSignal(value, "time_element", 0.88, text or value)

    # 5) Generic visible-DOM detector. It ranks date-shaped text by semantic
    # attributes and article/header proximity instead of relying on a site's CSS.
    candidates = []
    for tag in soup.find_all(["time", "span", "p", "div"]):
        has_semantic_attribute = any(tag.get(key) for key in ("class", "id", "itemprop", "data-testid", "data-test"))
        if tag.name != "time" and not has_semantic_attribute:
            continue
        candidate = _visible_date_candidate(tag)
        if candidate is not None:
            candidates.append(candidate)
    if candidates:
        score, value, evidence = max(candidates, key=lambda item: item[0])
        confidence = min(0.94, 0.78 + 0.02 * score)
        return PublicationDateSignal(value, "visible_dom", confidence, evidence)

    return PublicationDateSignal(None, None, 0.0)
