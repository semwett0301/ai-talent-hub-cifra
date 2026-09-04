# parse

Pure recognition logic — no I/O, no `crawl4ai` import. Takes a link or a page's
already-fetched text and answers a yes/no/what question about it. Used by
`SourceService.__detect_type` to pick a source's `SourceType` (and, for RSS, the
concrete feed URL) without the caller knowing how detection works.

- `telegram.py` — `is_telegram_link(link)`: `tg://` deep links or
  `https://t.me/` / `https://telegram.me/` links.
- `rss.py` — `RssFeedLink` (the discovered feed URL) + `find_rss_feed_link(page_content,
  base_url)`: a `<link rel="alternate" type="application/rss+xml|atom+xml">` in the
  page, or the page itself already being a raw RSS/Atom document.

Notes: `find_rss_feed_link` only inspects text already fetched by the `PageFetcher`
port (`application/ports/crawler.py`) — it never fetches anything itself, so it stays
testable without network access.
