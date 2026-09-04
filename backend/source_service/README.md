# source_service

Ingestion service: **CRUD sources → collect news → publish to RabbitMQ**. No
dedupe, no news storage — downstream consumes from RabbitMQ. Pull collectors
(RSS/Web) are **stubs**; the Telegram push collector is **implemented** (kurigram).
Design: `../../../plans/source-service-architecture.md`,
`../../../plans/telegram-kurigram-migration.md`.

Structured as **onion architecture** (layers depend inward; see `../README.md`):

- `Dockerfile` — image (FastAPI + Uvicorn). Multi-stage: uv builds a self-contained
  `.venv`, copied onto a clean `python:3.12-slim`. Migrations live in `migrator`.
- `pyproject.toml` — deps on `domain` + fastapi, aio-pika, apscheduler, kurigram.
  Ships a uniquely named top-level package `source_service`.
- `source_service/`
  - `main.py` — FastAPI app + lifespan; builds collaborators via `deps` and runs
    them. Routers own paths from the root; nginx maps `/api/sources/*` onto them, so
    the OpenAPI spec is reachable at `/api/sources/openapi.json`. (No `root_path`, so
    the Swagger UI at `/api/sources/docs` won't auto-load the spec through nginx —
    use it against the service directly in dev.)
  - `deps.py` — **composition root**: builds collector registries + repository +
    publisher and injects them into application (all DI lives here). Data shapes are
    shared: `Source` (ORM) from `domain.schemas`, `NewsDTO` from `domain.entities.news`.
  - `application/` — `ports/` (interfaces infra implements) + `dto/` + `services/`:
    `SourceService` (CRUD over the repo port) and `SourceRegistry` (the runtime
    registrar — pull scheduling + push subscription, kept in sync with CRUD).
  - `infrastructure/` — port implementations: `repositories/` (`SourceRepo`, a
    session per call), `rabbit/` (`RabbitConnector`), `collectors/`
    (`Rss`/`WebCrawl`/`Telegram`).
  - `api/routes/` — FastAPI routers only: `sources.py` (CRUD), `health.py`.

Notes: pull collectors run on `poll_interval_seconds` (default 300s); push sources
are subscribed at startup. CRUD stays live — create/update/delete reconcile the
runtime through the `SourceRegistry` composite (stored on `app.state.registrar`), so
sources (un)schedule/(un)subscribe without a restart. Filling in a collector =
implement `fetch`/`subscribe` in its infra file; register it in `deps`.
The `Source` table and every ORM model live in the shared `domain.schemas` (one DB for
all services); the DB schema history is applied by `../migrator`.
