# infrastructure

Implementations of the application ports plus adapters to the outside world (DB,
message bus, external sources). Depends on `application` (the ports) and `common`;
nothing depends inward on it except the composition root (`deps.py`).

- `repositories/` — `SourceRepo` over the ORM, a session per call (the `Source`
  table itself lives in `common/schemas/`).
- `rabbit/` — `RabbitConnector`, the `NewsPublisher` implementation.
- `collectors/` — `Pull`/`PushCollector` implementations (RSS, Web, Telegram).
- `scheduling/` — `ApSchedulerJobs`, the `JobScheduler` implementation on APScheduler's
  `AsyncIOScheduler`. The only place that knows about job ids and `replace_existing`; owns
  the `start`/`shutdown` lifecycle `main.py` drives around serving.
- `crawlers/` — the HTTP-facing adapters: `Crawl4AiPageFetcher` (`PageFetcher`, the
  one HTTP fetch in the service — feed XML, article HTML) and `FeedparserFeedReader`
  (`FeedReader`, parses the fetched feed) behind `RssCollector`.
- `parsing/` — `FeedsearchRssFeedFinder` (`RssFeedFinder`): feed discovery for
  `SourceService`'s type auto-detection, on `feedsearch_crawler` (its own HTTP session
  per call).

Notes: classes here implement the ports (they inherit the `Protocol`); `deps.py`
constructs them and injects them where a port is expected. Adapters that need HTTP
take the `PageFetcher` port rather than opening their own client — one place owns
timeouts, headers, and the session lifecycle. DB engine/session come
from `common.core.db`.
