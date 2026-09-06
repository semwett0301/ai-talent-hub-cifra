# news_service

Consumer service: **RabbitMQ `news` exchange → batch → `news` table**, plus a read API:
list the feed (search, period, hidden items), open one item, **dismiss** / **restore** it
(`dismissed_at`), or **escalate** it into a legislative act — flag `is_alert` + a
synchronous create in `npa_service`, committed only when that service confirmed. Every `NewsDTO` published by `source_service` is stored as-is —
one flat row, no JSON blob — once per `url` (the DB's unique key — a story arriving twice,
or from two sources, lands once); an item whose source was deleted while the batch was in
flight is skipped with a WARNING, since a row needs its source. Design: `../../plans/news-service.md`, escalation: `../../plans/npa-service.md`.

Structured as **onion architecture** (layers depend inward; see `../README.md`):

- `Dockerfile` — image (FastAPI + Uvicorn). Multi-stage: uv builds a self-contained
  `.venv`, copied onto a clean `python:3.12-slim`. Migrations live in `migrator`.
- `pyproject.toml` — deps on `common` + fastapi, uvicorn, aio-pika, httpx (the call
  to `npa_service`). Ships a uniquely named top-level package `news_service`.
- `news_service/`
  - `main.py` — FastAPI app + lifespan; starts/stops the consumer built by `deps`.
    Routers own paths from the root; nginx maps `/api/news/*` onto them
    (`root_path = settings.news_api_prefix`, so `/api/news/docs` works behind nginx).
  - `deps.py` — **composition root**: scopes the unit of work and builds everything on it.
    `get_news_repo` is a `yield` dependency — one DB session per HTTP request, closed
    (rolled back unless committed) after the response; `get_news_feed` /
    `get_npa_escalation` (with `HttpNpaGateway` on `settings.npa.npa_service_url`) take
    the `NewsRepo` from it, so one request = one session. `BatchScope` does the same per
    consumed batch for the shared `common.core.rabbit.RabbitBatchConsumer[NewsDTO]` (bound
    with `NEWS_BINDING_KEY` = `news.raw.#`), wrapping `NewsIngestor`.
  - `application/` — `ports/` (`NewsRepository`, `NewsBatchHandler`, `NpaGateway`) + `dto/news/` (`NewsQuery` in, `NewsOut` out) + `services/`
    (`NewsFeed` list/get/dismiss/restore, `NewsIngestor` batch store, `NpaEscalation` flag
    + register act) + `errors.py`.
  - `infrastructure/` — port implementations: `repositories/` (`NewsRepo` over the one
    session it is given; writes stage, `commit()` persists) and `gateways/`
    (`HttpNpaGateway` → `npa_service`). No rabbit code here —
    the batching consumer is the shared one in `common/core/rabbit/`.
  - `api/routes/` — FastAPI routers only: `news.py` (`GET /`, `GET /{id}`,
    `POST /{id}/dismiss`, `POST /{id}/restore`, `POST /{id}/npa`), `health.py`.

Notes: batching (in `common.core.rabbit`) = `prefetch_count == NEWS_BATCH_SIZE` (100)
+ a flush every `NEWS_BATCH_INTERVAL_SECONDS` (60) **or** when the buffer is full,
whichever first — one session and one transaction per batch (`BatchScope`), the ingestor
commits, acks only after that, nack on `NewsStoreError` (a `BatchStoreError`) — requeued while `NEWS_REQUEUE_ON_STORE_ERROR`
is `true` (default), dropped otherwise.
Escalation (`POST /{id}/npa`, optional body = `common.entities.npa.NpaDTO`, else the act
is built from the news item) runs inside the request's one session: stage `is_alert =
true` → POST the act to `npa_service` → `commit()`; if the call fails or is refused the use
case never reaches `commit()`, the session closes uncommitted and the flag stays unset (**409** for a duplicate `url`, **502** when
`npa_service` is unreachable / errors). Hiding is separate: `dismissed_at` is set by
`POST /{id}/dismiss`, cleared by `POST /{id}/restore`, and `GET /` shows only unhidden items
unless `visibility=dismissed` (only hidden) or `all`.
The `News` table and every ORM model live in the shared `common.schemas` (one DB for
all services); the DB schema history is applied by `../migrator`.
