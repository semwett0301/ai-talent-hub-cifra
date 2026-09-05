# services

Application services — use cases and orchestration, **grouped by domain** the way
`source_service/domain` is. Each subpackage re-exports its classes from `__init__.py` and
has its own README; nothing lives at the root of `services/`.

- `source/` — `SourceService` (CRUD + type auto-detection) and `SourceRegistry` (the
  runtime registrar: pull scheduling + push subscription).
- `scraping/` — how to reach a site's publications: `WebCrawl` (orchestrator),
  `HubDiscovery`, `CardCollection`, `ArticleFetching`.
- `article/` — what happens to a fetched article: `DateResolution`, `ArticleJudgement`
  (+ `LlmDateBudget`).

Notes: a service takes its collaborators as ports and its knobs as one settings group in
the constructor, and exposes one `run`. Between the crawl services articles travel as
`Article`, and the contract is the status — a service accepts one status and returns the
next (or `REJECTED` with a reason). A new area = a new subpackage, not a file here.
