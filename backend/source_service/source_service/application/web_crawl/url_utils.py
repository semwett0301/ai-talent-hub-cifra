from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "yclid",
    "_ga",
    "ref",
    "source",
}

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
ARTICLE_TERMS = (
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
LISTING_OR_JUNK_TERMS = (
    "/tag/",
    "/tags/",
    "/category/",
    "/categories/",
    "/author/",
    "/authors/",
    "/search",
    "/calendar",
    "/contacts",
    "/contact",
    "/about",
    "/products",
    "/services",
    "/catalog",
    "/vacanc",
    "/career",
    "/login",
    "/privacy",
    "/terms",
    "/newsletter",
    "/subscription",
    "/subscribe",
    "/feed",
    "/taxonomy/",
    "/events",
    "/event/",
)
DATE_IN_URL_RE = re.compile(r"/(20\d{2})[/-](0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])(?:/|$)")
NUMERIC_ID_RE = re.compile(r"/(?:\d{5,})(?:/|\.html?$|$)", re.I)
LONG_SLUG_RE = re.compile(r"/[a-zа-я0-9][a-zа-я0-9_-]{18,}(?:/|\.html?$|$)", re.I)


def normalize_url(url: str, base: str | None = None) -> str:
    absolute = urljoin(base, url) if base else url
    parsed = urlparse(absolute)
    if parsed.scheme.lower() not in {"http", "https"}:
        return ""
    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ]
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunparse(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, "", urlencode(query), "")
    )


def host_matches(url: str, allowed_domains: list[str], seed_url: str) -> bool:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    seed_host = (urlparse(seed_url).hostname or "").lower().removeprefix("www.")
    domains = [d.lower().strip().removeprefix("www.") for d in allowed_domains if d.strip()] or [
        seed_host
    ]
    return any(host == d or host.endswith("." + d) for d in domains)


def hub_score(url: str, title: str = "", text: str = "") -> float:
    hay = f"{url} {title}".lower()
    path = urlparse(url).path.lower()
    score = 0.0
    if any(term in hay for term in HUB_TERMS):
        score += 0.55
    depth = len([x for x in path.split("/") if x])
    if depth <= 2:
        score += 0.12
    if any(term in hay for term in LISTING_OR_JUNK_TERMS):
        score -= 0.55

    # Strong article-shaped URLs should not become listing hubs merely because
    # their path contains /news/. This is a ranking penalty, not a hard ban.
    if DATE_IN_URL_RE.search(url):
        score -= 0.42
    if NUMERIC_ID_RE.search(path):
        score -= 0.30
    if LONG_SLUG_RE.search(path) and depth >= 3:
        score -= 0.24
    if depth >= 5:
        score -= 0.10

    # Listing pages often expose many dated cards/headlines. This is only a weak signal.
    prefix = (text or "")[:9000]
    date_hits = len(re.findall(r"\b(?:20\d{2}|\d{1,2}[./-]\d{1,2}[./-]20\d{2})\b", prefix))
    if date_hits >= 3:
        score += 0.16
    return max(0.0, min(1.0, score))


def article_score(
    url: str, title: str = "", context: str = "", metadata: dict | None = None
) -> float:
    path = urlparse(url).path.lower()
    score = 0.0
    if any(term in path for term in LISTING_OR_JUNK_TERMS):
        score -= 0.45
    if any(term in path for term in ARTICLE_TERMS):
        score += 0.24
    if DATE_IN_URL_RE.search(url):
        # Date in URL is useful for candidate discovery, but is NOT trusted as publication date.
        score += 0.22
    if NUMERIC_ID_RE.search(path):
        score += 0.18
    if LONG_SLUG_RE.search(path):
        score += 0.16
    depth = len([x for x in path.split("/") if x])
    if depth >= 2:
        score += 0.08
    if depth >= 3:
        score += 0.05
    if len((title or "").strip()) >= 20:
        score += 0.10
    if len((context or "").strip()) >= 30:
        score += 0.04
    md = metadata or {}
    meta_text = " ".join(str(v) for v in md.values() if isinstance(v, (str, int, float))).lower()
    if "article" in meta_text or "newsarticle" in meta_text:
        score += 0.18
    return max(0.0, min(1.0, score))
