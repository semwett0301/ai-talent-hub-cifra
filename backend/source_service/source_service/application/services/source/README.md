# services/source

Sources as records and as a running schedule — one public class per module,
re-exported from `__init__.py`.

- `source_service.py` — `SourceService`: CRUD use-cases over `SourceRepository`; each
  mutation reconciles the runtime through the injected `SourceRegistry`. `create`
  and (when `link` changes) `update` auto-detect `type` — a Telegram link by
  `application.parse`, anything else by asking the injected `RssFeedFinder` for the
  site's feeds — clients never send `type`. Every RSS feed found is stored as an
  `RssLink` row (server-only, never accepted from a client), written by the repository
  in the same transaction as the source; a changed `link` replaces the whole list.
  `link` itself is never rewritten. The detected type
  also decides the **schedule**: a push source (Telegram) gets `poll_interval_seconds
  = null`, a pull source keeps the interval it already had and otherwise starts on
  `SourceSchedulerSettings.source_poll_interval_seconds` — clients pick an interval
  only by PATCHing an existing row, never on create. `is_relevant` is not
  client-settable either (only `WebCrawlCollector` sets it false); `update` rejects
  a PATCH that would enable a source still marked `is_relevant=false` (409/422 via
  `api/errors.py`), and the DB CHECK constraint backs this up regardless of who
  writes the row. **A changed `link` resets `is_relevant` to true** — the verdict
  belonged to the old address — so editing a source is the way out of that state,
  and a bare `is_enabled` PATCH still hits the refusal. Only a source that verdict
  had force-disabled is switched back on with it; one the operator disabled stays
  off, and a PATCH that leaves `link` alone touches neither flag.
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
