# parse

Pure text-in/structure-out logic — no network I/O. Takes a link or a page's
already-fetched text and turns it into an answer or a structure. Parsing *tools*
(news-please) live here; *connectors* to the outside world (crawl4ai, feedparser's
fetch) do not.

Recognition, used by `SourceService.__detect_type` to pick a source's `SourceType`
(and, for RSS, the concrete feed URL):

- `telegram.py` — `is_telegram_link(link)`: `tg://` deep links or
  `https://t.me/` / `https://telegram.me/` links.
- `rss.py` — `RssFeedLink` (the discovered feed URL) + `find_rss_feed_link(page_content,
  base_url)`: a `<link rel="alternate" type="application/rss+xml|atom+xml">` in the
  page, or the page itself already being a raw RSS/Atom document.

Extraction, used by `RssCollector` for each feed entry's full text:

- `article.py` — `ExtractedArticle` (title/text/published_at) +
  `extract_article(html, url)`: news-please's deterministic stack (newspaper4k +
  readability + date heuristics, no LLM) over an already-fetched page. `None` (never
  raises) when nothing usable came out; the `url` sharpens date extraction.

Notes: nothing here fetches — callers hand in text already fetched through the
`PageFetcher` port (`application/ports/crawler.py`), so it all stays testable without
network access. `extract_article` uses only `NewsPlease.from_html`, never
`from_url`/`from_urls`: those go through news-please's `SimpleCrawler`, which stores
results in a class-level dict and resets it per call, so concurrent calls silently come
back empty. The empty result is `{}`, detected with `isinstance(_, dict)` — **not**
`isinstance(_, NewsArticle)`: news-please imports that class under a bare `NewsArticle`
module name, so the check against `newsplease.NewsArticle.NewsArticle` is always
`False`. It is blocking (lxml, ~0.2s/article) — on the event loop run it via
`asyncio.to_thread`, as `RssCollector` does. This is the only place in the service
that imports `newsplease`.
