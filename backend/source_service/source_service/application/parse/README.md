# parse

Pure text-in/structure-out logic — no network I/O. Takes a link or a page's
already-fetched text and turns it into an answer, a structure or a domain object. Parsing
*tools* (news-please, BeautifulSoup, dateutil) live here; *connectors* to the outside world
(crawl4ai, feedparser's fetch, LiteLLM) do not.

Grouped into three subpackages by who calls them; each has its own `README.md` and re-exports
its own public API, and the top-level `__init__.py` re-exports all three so callers keep
importing from `source_service.application.parse`:

- `detection/` — link-kind recognition (Telegram), used by `SourceService.__detect_type`;
  feed discovery is the `RssFeedFinder` port, not parsing.
- `extraction/` — full article-text extraction, used by `RssCollector`.
- `reading/` — date/listing/article-page parsing, used by the WEB crawl services.

Notes: nothing here fetches — callers hand in text already fetched through a port, so it
all stays testable without network access. Modules within one subpackage import each other
directly (`from .dates import parse_date`), not through the package, to avoid import cycles —
only cross-subpackage and cross-package imports go through an `__init__.py`.
