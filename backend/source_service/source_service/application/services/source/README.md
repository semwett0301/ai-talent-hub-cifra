# services/source

Sources as records and as a running schedule — one public class per module,
re-exported from `__init__.py`.

- `source_service.py` — `SourceService`: CRUD use-cases over `SourceRepository`; each
  mutation reconciles the runtime through the injected `SourceRegistry`. `create`
  and (when `link` changes) `update` auto-detect `type` via the injected
  `PageFetcher` + `application.parse` — clients never send `type`. When the
  detected feed is RSS, the feed URL is stored in `rss_link` (also server-only,
  never accepted from a client); `link` itself is never rewritten. `is_relevant` is
  not client-settable either (only `WebCrawlCollector` sets it); `update` rejects
  (`ValueError`, turned into a 422 at the route) a PATCH that would enable a source
  already marked `is_relevant=false` — the DB CHECK constraint backs this up
  regardless of who writes the row.
- `source_registry.py` — `SourceRegistry`: what a source's runtime state should be.
  Dispatches by source type — pull → a job through the `JobScheduler` port, push →
  subscription — and applies `is_enabled` in both directions. Takes its collectors and the
  publisher as one `SourceCollectors`, plus the scheduler port, the repository and
  `SourceSchedulerSettings` (the fallback poll interval). `load` bootstraps every enabled
  source at startup; `__run` is the pull use case itself: re-read the source, skip with a
  reason if it is gone or disabled, fetch, publish.

Notes: collaborators are injected from the root `deps.py`, never bare callables or
concrete infra — with one deliberate exception, `SourceService` takes `SourceRegistry`
itself: both live here, so a protocol between two siblings of the same layer would invert
nothing. The registry holds **no** scheduling mechanics and no lifecycle of its own: the
scheduler is a port, and `start`/`shutdown` belong to its adapter, driven by `main.py`.
`register`/`unregister` is the single per-source path — CRUD calls it for one source (via
`app.state.registrar`), startup `load` calls it for every enabled source. The `SourceRepo`
opens a session per call — safe for this long-lived, concurrent service.
