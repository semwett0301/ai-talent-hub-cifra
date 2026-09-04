# collectors

Collector implementations of the application collector ports — the per-source-type
"how to get news" (external I/O). Re-exported from `__init__.py`.

- `rss.py` — `RssCollector` (pull, feedparser). **Stub**.
- `web.py` — `WebCrawlCollector` (pull, crawl4ai/Playwright). **Stub**.
- `telegram.py` — `TelegramCollector` (push, kurigram — a Pyrogram fork, imported as
  `pyrogram`): joins channels and publishes each new post as a `NewsItem` via the
  injected `NewsPublisher`. **Implemented.**

Notes: each collector **inherits its port** (`PullCollector` / `PushCollector`) so mypy
verifies conformance at the definition site (nominal + structural double guard).
`TelegramCollector` also needs the `NewsPublisher` port and Telegram creds, so it's built
per-run in `deps.build_telegram_collector` (not a constant) and owns a client lifecycle
(`start`/`stop`) driven by the `main` lifespan; it degrades to a no-op when creds/session
are absent. The pull registry lives in `deps.py`.
