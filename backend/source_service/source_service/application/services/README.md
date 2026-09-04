# services

Application services — use cases and background aggregators, one public class per
module (re-exported from `__init__.py`).

- `source_service.py` — `SourceService`: CRUD use-cases over `SourceRepository`; each
  mutation reconciles the runtime through the injected `SourceRegistrar`. `create`
  and (when `link` changes) `update` auto-detect `type` via the injected
  `PageFetcher` + `application.parse` — clients never send `type`.
- `source_registry.py` — `SourceRegistry`: the sole `SourceRegistrar`. Dispatches by
  source type — pull → APScheduler job, push → subscription; injected publisher +
  pull/push collectors + `SourceRepository`. Owns `start`/`shutdown`/`load` lifecycle
  (used by `main.py`, off the port).

Notes: collaborators are injected from the root `deps.py` as ports (interfaces),
never bare callables or concrete infra. `register`/`unregister` is the single
per-source path — CRUD calls it for one source (via `app.state.registrar`), startup
`load` calls it for every enabled source. The `SourceRepo` opens a session per call —
safe for this long-lived, concurrent service. Started from `main.py`'s lifespan.
