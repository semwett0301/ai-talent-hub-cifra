# crawling

The `PageFetcher` port implementation. The only place in the service that imports
`crawl4ai`.

- `crawl4ai_fetcher.py` — `Crawl4AiPageFetcher`: wraps `AsyncWebCrawler` with
  `AsyncHTTPCrawlerStrategy` (lightweight HTTP fetch, no Playwright/browser) to
  fetch a page's HTML. Owns a `start`/`close` lifecycle, driven from `main.py`'s
  lifespan (same pattern as `RabbitConnector`/`TelegramCollector`).

Notes: `fetch` never raises — a failed crawl (network error or `result.success is
False`) returns `None`, so `SourceService.__detect_type` can uniformly fall back to
`SourceType.WEB` without a `try`/`except` of its own.
