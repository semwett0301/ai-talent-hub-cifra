# application

Use-case / orchestration layer. Coordinates via **ports** (interfaces it defines and
infrastructure implements); depends on the shared `domain` package (schemas +
entities), never on concrete infra. Collaborators are injected by the composition
root (`deps.py`).

- `ports/` — the interfaces (Protocols) infra/services implement: repositories,
  collectors, publisher, registrar, crawler (page fetcher), feed reader.
- `dto/` — request/response DTOs (Pydantic) for the use cases.
- `services/` — `SourceService` (CRUD use case) and `SourceRegistry` (the runtime
  registrar: pull scheduling + push subscription), one class per module.
- `parse/` — pure text-in/structure-out logic (no I/O): link/page recognition for
  `SourceService`'s type auto-detection, and article extraction (news-please) for
  `RssCollector`.

Notes: import ports (`application.ports`), not infra classes. `SourceRegistry` is
built in `deps.py` and started from `main.py`'s lifespan. `parse/` has no port of
its own — it's plain functions `SourceService` calls directly, not something
infrastructure implements.
