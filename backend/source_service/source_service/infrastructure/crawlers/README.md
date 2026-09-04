# crawlers

The HTTP-facing adapters: the `PageFetcher` port implementation and the `FeedReader`
that parses what it fetches. The only place in the service that imports `crawl4ai`
and `feedparser`.

- `crawl4ai_fetcher.py` — `Crawl4AiPageFetcher`: wraps `AsyncWebCrawler` with
  `AsyncHTTPCrawlerStrategy` (lightweight HTTP fetch, no Playwright/browser) to
  fetch a URL's raw body — page HTML, or feed XML (non-HTML text comes back as-is).
  Owns a `start`/`close` lifecycle, driven from `main.py`'s lifespan (same pattern
  as `RabbitConnector`/`TelegramCollector`).
- `feedparser_reader.py` — `FeedparserFeedReader(page_fetcher)`: fetches the feed body
  through `PageFetcher`, parses it with feedparser inline (tens of ms per feed, once
  per pull — no worker thread) and maps each item to a `FeedEntry` (markup stripped
  from title/summary, `published_parsed`/`updated_parsed` → aware UTC datetime).
  `read` never raises — a failed fetch returns `[]`, a feed with XML errors (`bozo`)
  still yields whatever parsed, both logged as WARNING. Items without a `link` are
  dropped: `url` is the dedupe key downstream. feedparser never fetches the URL
  itself (its urllib fetch has no timeout).

Notes: the one HTTP client in the service — `SourceService` (type auto-detection),
`FeedparserFeedReader`, and `RssCollector` (article pages) all fetch through it, so
timeouts and headers live in one place. `fetch` never raises — a failed crawl
(network error or `result.success is False`) returns `None`, so callers fall back
(`SourceType.WEB`, empty feed, feed summary) without a `try`/`except` of their own.
Runs with `verbose=False`: crawl4ai otherwise narrates every fetch to stdout, and
RSS pulls fetch hundreds of articles.
