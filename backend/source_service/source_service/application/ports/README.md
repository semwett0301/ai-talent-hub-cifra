# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). **Grouped by domain**, the way
`services/` is; each subpackage re-exports its ports from `__init__.py` and has its own
README, nothing lives at the root. One port per implementation: two services sharing one
adapter share one interface.

- `source/` — `SourceRepository`, `JobScheduler`, `PullCollector` / `PushCollector`,
  `NewsPublisher`: sources as records, as a running schedule, and the news they produce.
- `scraping/` — `PageFetcher`, `RssFeedFinder`, `FeedReader` (+ `FeedEntry`), `PageCrawler` (+ `FetchedPage`,
  `PageLink`) and `CrawlLlm` (+ `ListingVerdict`, `DateGuess`): reaching pages, feeds and
  sites, and the two questions the crawl asks a language model.

Notes: import from the subpackage (`from source_service.application.ports.scraping import
PageCrawler`). Ports reference the `common.schemas` `Source` and the shared
`common.entities.news.NewsDTO` contract directly. Fetching ports **never raise** — a
failure is `None` / `[]` / a missing page plus a WARNING at the adapter; the LLM port
returns `None` on a failed or invalid answer. Parsing is not a port: it is pure logic in
`application/parse`.
