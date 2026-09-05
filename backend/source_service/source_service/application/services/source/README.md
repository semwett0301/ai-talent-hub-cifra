# services/source

Sources as records and as a running schedule — one public class per module,
re-exported from `__init__.py`.

- `source_service.py` — `SourceService`: CRUD use-cases over `SourceRepository`; each
  mutation reconciles the runtime through the injected `SourceRegistrar`. `create`
  and (when `link` changes) `update` auto-detect `type` via the injected
  `PageFetcher` + `application.parse` — clients never send `type`. When the
  detected feed is RSS, the feed URL is stored in `rss_link` (also server-only,
  never accepted from a client); `link` itself is never rewritten.
- `source_registry.py` — `SourceRegistry`: the sole `SourceRegistrar`. Dispatches by
  source type — pull → APScheduler job, push → subscription; injected publisher +
  pull/push collectors + `SourceRepository`. Owns `start`/`shutdown`/`load` lifecycle
  (used by `main.py`, off the port).

Notes: collaborators are injected from the root `deps.py` as ports (interfaces),
never bare callables or concrete infra. `register`/`unregister` is the single
per-source path — CRUD calls it for one source (via `app.state.registrar`), startup
`load` calls it for every enabled source. The `SourceRepo` opens a session per call —
safe for this long-lived, concurrent service. Started from `main.py`'s lifespan.
