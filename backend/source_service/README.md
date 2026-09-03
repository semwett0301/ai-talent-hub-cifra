# source_service

Ingestion service: **CRUD sources → collect news → publish to RabbitMQ**. No
dedupe, no news storage — downstream consumes from RabbitMQ. Collectors are
**stubs** for now (return no items). Design:
`../../../plans/source-service-architecture.md`.

Structured as **onion architecture** (layers depend inward; see `../README.md`):

- `Dockerfile` — image (FastAPI + Uvicorn). Multi-stage: uv builds a self-contained
  `.venv`, copied onto a clean `python:3.12-slim`. Migrations live in `migrator`.
- `pyproject.toml` — deps on `common` + fastapi, aio-pika, apscheduler. Ships a
  uniquely named top-level package `source_service`.
- `source_service/`
  - `main.py` — FastAPI app + lifespan; builds collaborators via `deps` and runs them.
  - `deps.py` — **composition root**: builds collector registries + repository +
    publisher and injects them into application (all DI lives here).
  - `domain/entities/` — business entities (`NewsItem`); no I/O, no dependencies.
  - `application/` — `ports/` (interfaces infra implements) + `dto/` + `services/`:
    `SourceService` (CRUD over the repo port), `SchedulerService` (pull aggregator),
    `SubscriptionService` (push aggregator).
  - `infrastructure/` — port implementations: `persistence/schemas/` (ORM `Source`),
    `persistence/repositories/` (`SourceRepo`), `rabbit/` (`RabbitConnector`),
    `collectors/` (`Rss`/`WebCrawl`/`Telegram`).
  - `api/routes/` — FastAPI routers only: `sources.py` (CRUD), `health.py`.

Notes: pull collectors run on `poll_interval_seconds` (default 300s); push sources
are subscribed at startup. Live (re)scheduling on CRUD is a TODO. Filling in a
collector = implement `fetch`/`subscribe` in its infra file; register it in `deps`.
This service owns the `Source` table; the DB schema history lives in `../migrator`.
