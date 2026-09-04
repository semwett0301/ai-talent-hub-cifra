# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). Re-exported from `__init__.py`.

- `collectors.py` — `PullCollector` (`fetch`), `PushCollector` (`subscribe`/
  `unsubscribe`).
- `repositories.py` — `SourceRepository`: `list_all` / `get` / `list_enabled(type)` +
  create/update/delete over sources.
- `publisher.py` — `NewsPublisher`: publishes `domain.entities.news.NewsDTO`s to the bus.
- `registrar.py` — `SourceRegistrar` (`register`/`unregister`): reconciles one source
  to the runtime. Implemented by `SourceRegistry`; injected into `SourceService` so
  CRUD stays live.
- `crawler.py` — `PageFetcher` (`fetch`): fetches a URL's raw body (page HTML, feed
  XML) for `SourceService`'s type auto-detection and for `RssCollector`'s article
  pages; implemented by `Crawl4AiPageFetcher`.
- `feed.py` — `FeedReader` (`read`) + its return shape `FeedEntry` (url/title/
  summary/published_at): downloads and parses one RSS/Atom feed for `RssCollector`;
  implemented by `FeedparserFeedReader`.

Notes: ports reference the `domain.schemas` `Source` and the shared
`domain.entities.news.NewsDTO` contract directly. The repository method is `list_all` (not
`list`) so the name doesn't shadow the builtin `list[...]` used in return annotations.
`PageFetcher` and `FeedReader` have no domain type in their signatures — they deal in
plain URLs, text and their own small frozen dataclasses. Both `PageFetcher.fetch` and
`FeedReader.read` **never raise**: a failure is `None` / `[]` plus a WARNING at the
adapter, so a caller needs no `try` of its own. Article extraction is not a port: it is
pure parsing over fetched text (`application/parse/article.py`).
