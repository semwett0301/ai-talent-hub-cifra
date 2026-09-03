# collectors

Collector implementations of the application collector ports — the per-source-type
"how to get news" (external I/O). Re-exported from `__init__.py`.

- `rss.py` — `RssCollector` (pull, feedparser). **Stub**.
- `web.py` — `WebCrawlCollector` (pull, crawl4ai/Playwright). **Stub**.
- `telegram.py` — `TelegramCollector` (push, aiogram). **Stub**.

Notes: each class structurally satisfies `application.ports.collectors` (no import of
the port). The `SourceType → collector` registries are assembled in the root `deps.py`,
not here. Filling in a collector = implement `fetch`/`subscribe`; register in `deps`.
