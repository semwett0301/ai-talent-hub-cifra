# services/dedup

Shared across pull collectors, whatever the source type: dropping what a poll found but
the shared `news` table already holds, before any page is fetched for it.

- `stored_news_filter.py` — `StoredNewsFilter.unstored(source_link, items) -> list[items]`:
  filters any list of URL-bearing items (an RSS `FeedEntry`, a web `Article` candidate, ...)
  against the `StoredNewsIndex` port and logs one `"<kind> entries filtered"` line. `kind`
  (`"rss"`, `"web"`) is fixed at construction — one instance per collector type.

Notes: this is the one thing genuinely common to every collector (rule `80-domain`) — the
filtering rule itself is generic, only the item type and the log label differ per caller.
Used by `infrastructure.collectors.RssCollector` and `application.services.web.WebCrawl`.
