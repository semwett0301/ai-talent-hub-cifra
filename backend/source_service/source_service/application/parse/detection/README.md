# parse/detection

Recognise a link's kind before any crawling. Used by `SourceService.__detect_type` to pick
a source's `SourceType` (and, for RSS, the concrete feed URL).

- `telegram.py` — `is_telegram_link(link)`: `tg://` deep links or
  `https://t.me/` / `https://telegram.me/` links.
- `rss.py` — `RssFeedLink` (the discovered feed URL) + `find_rss_feed_link(page_content,
  base_url)`: a `<link rel="alternate" type="application/rss+xml|atom+xml">` in the page,
  or the page itself already being a raw RSS/Atom document.

Notes: both take already-fetched text, nothing here fetches.
