# collectors

Collector implementations of the application collector ports — the per-source-type
"how to get news" (external I/O). Re-exported from `__init__.py`.

- `rss.py` — `RssCollector` (pull). **Implemented.** Polls `source.rss_link` (the
  detected feed URL, distinct from `source.link`) through the `FeedReader` port, fetches
  every entry's page through the `PageFetcher` port and extracts its full text with
  `application.parse.extract_article` (news-please); falls back to the feed summary
  when extraction comes back empty. Emits one
  `NewsDTO` per entry with
  `url` = the entry's canonical link and `raw` = `{title, summary, feed_url}`.
- `web.py` — `WebCrawlCollector` (pull): turns the `Source` row into a domain `Site`, runs
  `application.services.scraping.WebCrawl` and emits each accepted `Article` via its own
  `to_news_dto(source)`. The browser it crawls with is an app-lifetime singleton.
- `telegram.py` — `TelegramCollector` (push, kurigram — a Pyrogram fork, imported as
  `pyrogram`): joins channels and publishes each new post as a `common.entities.news.NewsDTO`
  via the injected `NewsPublisher`. **Implemented.**

Notes: each collector **inherits its port** (`PullCollector` / `PushCollector`) so mypy
verifies conformance at the definition site (nominal + structural double guard).
`TelegramCollector` also needs the `NewsPublisher` port and Telegram creds, so it's built
per-run in `deps.build_telegram_collector` (not a constant) and owns a client lifecycle
(`start`/`stop`) driven by the `main` lifespan; it degrades to a no-op when creds/session
are absent. The pull registry lives in `deps.py`, where `RssCollector` is built with
`FeedparserFeedReader` and the app-scoped `PageFetcher`.
`RssCollector` keeps **no state**: every pull emits the feed's current entries and
forgets them — dedupe is downstream's job, on `NewsDTO.url`. Extractions run
at most `MAX_CONCURRENT_EXTRACTIONS` at a time per pull; the blocking news-please call
runs in a worker thread (`asyncio.to_thread`) so the event loop stays responsive.
