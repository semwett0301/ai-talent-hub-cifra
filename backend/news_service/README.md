# news_service

Consumer service: **RabbitMQ → summary checkpoint → event dedup → cluster ranking → DB**,
plus a read API:
list what's stored, dismiss an item (`is_alert = true`), or **escalate** it into a
legislative act — dismiss + a synchronous create in `npa_service`, committed only when
that service confirmed. Every `NewsDTO` published by `source_service` is stored as-is,
once per `url` (the DB's unique key — a story arriving twice, or from two sources,
lands once). Design: `../../plans/news-service.md`, escalation: `../../plans/npa-service.md`.

Structured as **onion architecture** (layers depend inward; see `../README.md`):

- `Dockerfile` — image (FastAPI + Uvicorn). Multi-stage: uv builds a self-contained
  `.venv`, copied onto a clean `python:3.12-slim`. Migrations live in `migrator`.
- `pyproject.toml` — deps on `common`, API/bus libraries, LangChain/OpenRouter,
  sentence-transformers, and pgvector through `common`.
- `news_service/`
  - `main.py` — FastAPI app + lifespan; starts/stops the consumer built by `deps`.
    Routers own paths from the root; nginx maps `/api/news/*` onto them
    (`root_path = settings.news_api_prefix`, so `/api/news/docs` works behind nginx).
  - `deps.py` — **composition root**: builds the read, dedup, and ranking repositories,
    model adapters, embedder, use cases, and the shared `RabbitBatchConsumer[NewsDTO]` (bound with
    `NEWS_BINDING_KEY` = `news.raw.#`); provides `get_news_feed` and
    `get_npa_escalation` (with `HttpNpaGateway` on `settings.npa.npa_service_url`) for the routes.
  - `application/` — ports, response DTOs, staged ingestion/dedup/ranking services,
    feed, and NPA escalation.
  - `domain/` — pure dedup and cluster-ranking entities/rules.
  - `infrastructure/` — repositories, OpenRouter models, the packaged GS Labs profile,
    local embeddings, and the NPA HTTP gateway.
  - `api/routes/` — FastAPI routers only: `news.py` (`GET /`, `POST /{id}/dismiss`,
    `POST /{id}/npa`), `health.py`.

Each unseen URL passes through batched primary-event extraction and a persisted per-news
summary. The summary checkpoint is committed before local embedding; the whole prepared batch
is then retrieved against the HNSW cosine index and conservatively aligned to candidate event
clusters. Each affected cluster is ranked as one object and upserted once into
`news_cluster_ranking`. A retry resumes without repeating completed summary or dedup checkpoints.

Notes: batching (in `common.core.rabbit`) = `prefetch_count == NEWS_BATCH_SIZE` (100)
+ a flush every `NEWS_BATCH_INTERVAL_SECONDS` (60) **or** when the buffer is full,
whichever first — one transaction per batch, acks only after commit, nack on
`BatchStoreError` — requeued while `NEWS_REQUEUE_ON_STORE_ERROR`
is `true` (default), dropped otherwise.
Escalation (`POST /{id}/npa`, body = `common.entities.npa.NpaDTO`) runs inside one DB
transaction: stage `is_alert = true` → POST the act to `npa_service` → commit; if the
call fails or is refused the transaction rolls back and the alert stays undismissed
(**409** for a duplicate `url`, **502** when `npa_service` is unreachable / errors).
The `News` table and every ORM model live in the shared `common.schemas` (one DB for
all services); the DB schema history is applied by `../migrator`.
