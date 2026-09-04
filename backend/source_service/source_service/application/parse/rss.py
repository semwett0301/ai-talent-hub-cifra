"""RSS-feed recognition inside a page's crawled content (HTML text in, feed URL out)."""

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin

_FEED_LINK_TYPES = {"application/rss+xml", "application/atom+xml"}
_FEED_ROOT_TAGS = ("<rss", "<feed")


@dataclass(frozen=True)
class RssFeedLink:
    url: str


class _FeedLinkParser(HTMLParser):
    """Collects the first `<link rel="alternate" type="application/(rss|atom)+xml">`."""

    def __init__(self) -> None:
        super().__init__()
        self.feed_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "link" or self.feed_href is not None:
            return

        attr_map = dict(attrs)
        if attr_map.get("rel") != "alternate" or attr_map.get("type") not in _FEED_LINK_TYPES:
            return

        self.feed_href = attr_map.get("href")


def find_rss_feed_link(page_content: str, base_url: str) -> RssFeedLink | None:
    """A feed `<link>` tag in the page, or the page itself being a raw RSS/Atom document."""
    stripped_content = page_content.lstrip()
    if _looks_like_feed_document(stripped_content):
        return RssFeedLink(url=base_url)

    parser = _FeedLinkParser()
    parser.feed(page_content)
    if parser.feed_href is None:
        return None

    return RssFeedLink(url=urljoin(base_url, parser.feed_href))


def _looks_like_feed_document(stripped_content: str) -> bool:
    if stripped_content.startswith(_FEED_ROOT_TAGS):
        return True

    if not stripped_content.startswith("<?xml"):
        return False

    after_declaration = stripped_content.split("?>", 1)[-1].lstrip()
    return after_declaration.startswith(_FEED_ROOT_TAGS)
