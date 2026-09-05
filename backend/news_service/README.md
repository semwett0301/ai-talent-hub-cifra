# news_service

Consumer service: **RabbitMQ `news` exchange → batch → `news` table**, plus a read API:
list what's stored, dismiss an item (`is_alert = true`), or **escalate** it into a
legislative act — dismiss + a synchronous create in `npa_service`, committed only when
that service confirmed. Every `NewsDTO` published by `source_service` is stored as-is,
once per `url` (the DB's unique key — a story arriving twice, or from two sources,
lands once). Design: `../../plans/news-service.md`, escalation: `../../plans/npa-service.md`.

Structured as **onion architecture** (layers depend inward; see `../README.md`):

- `Dockerfile` — image (FastAPI + Uvicorn). Multi-stage: uv builds a self-contained
  `.venv`, copied onto a clean `python:3.12-slim`. Migrations live in `migrator`.
- `pyproject.toml` — deps on `common` + fastapi, uvicorn, aio-pika, httpx (the call
  to `npa_service`). Ships a uniquely named top-level package `news_service`.
- `news_service/`
  - `main.py` — FastAPI app + lifespan; starts/stops the consumer built by `deps`.
    Routers own paths from the root; nginx maps `/api/news/*` onto them
    (`root_path = settings.news_api_prefix`, so `/api/news/docs` works behind nginx).
  - `deps.py` — **composition root**: builds `NewsRepo`, `NewsIngestor`, and the
    shared `common.core.rabbit.RabbitBatchConsumer[NewsDTO]` (bound with
    `NEWS_BINDING_KEY` = `news.raw.#`); provides `get_news_feed` and
    `get_npa_escalation` (with `HttpNpaGateway` on `settings.npa.npa_service_url`) for the routes.
  - `application/` — `ports/` (`NewsRepository`, `NewsTransaction`, `NewsBatchHandler`,
    `NpaGateway`) + `dto/news/` + `services/` (`NewsFeed` list/dismiss, `NewsIngestor`
    batch store, `NpaEscalation` dismiss + register act) + `errors.py`.
  - `infrastructure/` — port implementations: `repositories/` (`NewsRepo`, a session
    per call, one-statement batch insert; `SqlNewsTransaction` for the held-open unit
    of work) and `gateways/` (`HttpNpaGateway` → `npa_service`). No rabbit code here —
    the batching consumer is the shared one in `common/core/rabbit/`.
  - `api/routes/` — FastAPI routers only: `news.py` (`GET /`, `POST /{id}/dismiss`,
    `POST /{id}/npa`), `health.py`.

Notes: batching (in `common.core.rabbit`) = `prefetch_count == NEWS_BATCH_SIZE` (100)
+ a flush every `NEWS_BATCH_INTERVAL_SECONDS` (60) **or** when the buffer is full,
whichever first — one transaction per batch, acks only after commit, nack on
`NewsStoreError` (a `BatchStoreError`) — requeued while `NEWS_REQUEUE_ON_STORE_ERROR`
is `true` (default), dropped otherwise.
Escalation (`POST /{id}/npa`, body = `common.entities.npa.NpaDTO`) runs inside one DB
transaction: stage `is_alert = true` → POST the act to `npa_service` → commit; if the
call fails or is refused the transaction rolls back and the alert stays undismissed
(**409** for a duplicate `url`, **502** when `npa_service` is unreachable / errors).
The `News` table and every ORM model live in the shared `common.schemas` (one DB for
all services); the DB schema history is applied by `../migrator`.
