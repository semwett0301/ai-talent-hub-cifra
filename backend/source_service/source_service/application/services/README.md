# services

Application services, **grouped by domain** the way `source_service/domain` is: the use
cases plus the steps they are composed of. Only `SourceService` and `WebCrawl` are use
cases in the strict sense — something an actor asks for; the rest are the steps a use case
runs. A step still belongs here and not in the domain, because it holds ports (I/O) and
thresholds from settings. Each subpackage re-exports its classes from `__init__.py` and has
its own README; nothing lives at the root of `services/`.

- `source/` — `SourceService` (CRUD + type auto-detection) and `SourceRegistry` (the
  runtime registrar: pull scheduling + push subscription).
- `web/` — collecting news from a `WEB` source: `WebCrawl` (the use case) over three stage
  subpackages, `web/hubs/` (site → listing pages), `web/listings/` (those pages → candidate
  links) and `web/articles/` (candidate links → accepted articles).

Notes: a service takes its collaborators as ports and its knobs as one settings group in
the constructor, and exposes one `run`. Between the crawl services articles travel as
`Article`, and the contract is the status — a stage handles its own status and passes the
rest through. Anything scoped to one run (a frontier, an LLM budget, a stale streak) is
built inside `run()` and never injected: see each stage's `state/`. A new area = a new
subpackage, not a file here.
