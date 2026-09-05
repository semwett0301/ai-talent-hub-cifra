# services/web

Collecting news from a `WEB` source — the one use case, plus the stages it runs. The split
follows the crawl itself: find the pages that list publications (`hubs/`), read those lists
into links (`listings/`), then open the links (`articles/`).

- `web_crawl.py` — `WebCrawl.run(source) -> list[Article]`: the orchestrator, and nothing
  else. Builds the `Site` from the `Source` row, calls the five stages in order, applies the
  domain's `merge_duplicates` to what came out accepted and writes one `web crawl finished`
  line from `CrawlRun`. When the listing search finds no candidate at all it marks the
  source `is_relevant=false` itself — no fallback. Takes its stages as one `CrawlStages`
  plus the `SourceRepository` port (wired in `deps.py`) and **no settings at all**: every
  threshold belongs to a stage.
- `hubs/` — site → `list[Hub]`: `HubDiscovery`, `ListingClassifier`.
- `listings/` — hubs → candidate links: `CardCollection`.
- `articles/` — candidate links → accepted articles: `ArticleHarvest`, `DateResolution`,
  `ArticleJudgement`.

Notes: one class per module, collaborators in the constructor (ports + `WebCrawlSettings`),
one `run`. Between services articles travel as `Article` and the contract is the **status**:
a stage handles its own status and passes the rest through, so no caller sorts by status.
`FetchedPage` never leaves the service that fetched it. Anything scoped to one site — a
frontier, an LLM budget, a stale streak — is built inside `run()` and never injected: the
services are shared by every concurrent crawl (see each stage's `state/`). Ranking and every
judgement about an article or a hub are domain rules (`is_article_like`, `rank_hubs`,
`merge_duplicates`, `FreshnessWindow`); the services only pass the thresholds from settings.
