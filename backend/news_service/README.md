# news_service

Consumer service: **RabbitMQ `news` exchange → batch → `news` table**, plus a read API:
list what's stored and dismiss an item (`is_alert = true`). Every `NewsDTO` published by `source_service` is stored as-is,
once per `url` (the DB's unique key — a story arriving twice, or from two sources,
lands once). Design: `../../plans/news-service.md`.

Structured as **onion architecture** (layers depend inward; see `../README.md`):

- `Dockerfile` — image (FastAPI + Uvicorn). Multi-stage: uv builds a self-contained
  `.venv`, copied onto a clean `python:3.12-slim`. Migrations live in `migrator`.
- `pyproject.toml` — deps on `domain` + fastapi, uvicorn, aio-pika. Ships a uniquely
  named top-level package `news_service`.
- `news_service/`
  - `main.py` — FastAPI app + lifespan; starts/stops the consumer built by `deps`.
    Routers own paths from the root; nginx maps `/api/news/*` onto them
    (`root_path = settings.news_api_prefix`, so `/api/news/docs` works behind nginx).
  - `deps.py` — **composition root**: builds `NewsRepo`, `NewsIngestor`, and the
    shared `domain.core.rabbit.RabbitBatchConsumer[NewsDTO]` (bound with
    `NEWS_BINDING_KEY` = `news.raw.#`); provides `get_news_feed` for the routes.
  - `application/` — `ports/` (`NewsRepository`, `NewsBatchHandler`) + `dto/news/` +
    `services/` (`NewsFeed` list/dismiss, `NewsIngestor` batch store) + `errors.py`.
  - `infrastructure/` — port implementations: `repositories/` (`NewsRepo`, a session
    per call, one-statement batch insert). No rabbit code here — the batching
    consumer is the shared one in `domain/core/rabbit/`.
  - `api/routes/` — FastAPI routers only: `news.py` (`GET /`, `POST /{id}/dismiss`),
    `health.py`.

Notes: batching (in `domain.core.rabbit`) = `prefetch_count == NEWS_BATCH_SIZE` (100)
+ a flush every `NEWS_BATCH_INTERVAL_SECONDS` (15) **or** when the buffer is full,
whichever first — one transaction per batch, acks only after commit, nack on
`NewsStoreError` (a `BatchStoreError`) — requeued while `NEWS_REQUEUE_ON_STORE_ERROR`
is `true` (default), dropped otherwise.
The `News` table and every ORM model live in the shared `domain.schemas` (one DB for
all services); the DB schema history is applied by `../migrator`.
