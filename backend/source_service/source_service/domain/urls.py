"""URL identity rules: normalisation, same-site check, listing identity, pagination."""

import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

TRACKING_PARAMS = frozenset(
    {
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
)
PAGINATION_PARAMS = frozenset({"page", "p", "paged", "offset"})
HTTP_SCHEMES = frozenset({"http", "https"})
WWW_PREFIX = "www."


def normalize_url(url: str, base: str | None = None) -> str:
    """Canonical spelling of a link; `""` for anything that is not an http(s) URL."""
    parsed = urlparse(urljoin(base, url) if base else url)
    if parsed.scheme.lower() not in HTTP_SCHEMES:
        return ""

    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    ]
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")

    return urlunparse(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, "", urlencode(query), "")
    )


def host_matches(url: str, allowed_domains: list[str], seed_url: str) -> bool:
    """Same site: the host equals one of the allowed domains (default: the seed's host)
    or is one of its subdomains."""
    host = _bare_host(url)
    domains = [_bare_domain(domain) for domain in allowed_domains if domain.strip()] or [
        _bare_host(seed_url)
    ]
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def listing_identity(url: str) -> str:
    """Identity of a listing: its pagination variants are one and the same hub."""
    parsed = urlparse(normalize_url(url))
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query)
        if key.lower() not in PAGINATION_PARAMS
    ]
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode(query), ""))


def is_pagination_url(url: str) -> bool:
    return any(key.lower() in PAGINATION_PARAMS for key, _ in parse_qsl(urlparse(url).query))


def path_depth(url: str) -> int:
    return len([segment for segment in urlparse(url).path.split("/") if segment])


def _bare_host(url: str) -> str:
    return _bare_domain(urlparse(url).hostname or "")


def _bare_domain(domain: str) -> str:
    return domain.lower().strip().removeprefix(WWW_PREFIX)
