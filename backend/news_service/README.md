# news_service

Consumer service: **RabbitMQ `news` exchange → summary checkpoint → event dedup →
cluster ranking → DB**, plus a read API: list the feed (search, period, hidden items),
open one item, **dismiss** / **restore** it (`dismissed_at`), or **escalate** it into a
legislative act — flag `is_alert` + a synchronous create in `npa_service`, committed only
when that service confirmed. Every `NewsDTO` published by `source_service` is stored as
one flat row, no JSON blob, once per `url` (the DB's unique key — a story arriving twice,
or from two sources, lands once); an item whose source was deleted while the batch was in
flight is skipped with a WARNING, since a row needs its source. Design:
`../../plans/news-service.md`, escalation: `../../plans/npa-service.md`.

Structured as **onion architecture** (layers depend inward; see `../README.md`):

- `Dockerfile` — image (FastAPI + Uvicorn). Multi-stage: uv builds a self-contained
  `.venv`, copied onto a clean `python:3.12-slim`. Migrations live in `migrator`.
- `pyproject.toml` — deps on `common`, API/bus libraries, LangChain/OpenRouter and the
  `openrouter` SDK (embeddings), and pgvector through `common`. No local ML runtime.
- `news_service/`
  - `main.py` — FastAPI app + lifespan; starts/stops the consumer built by `deps`.
    Routers own paths from the root; nginx maps `/api/news/*` onto them
    (`root_path = settings.news_api_prefix`, so `/api/news/docs` works behind nginx).
  - `deps.py` — **composition root**, two independent halves. Read API: `get_news_repo`
    is a `yield` dependency — one DB session per HTTP request, closed (rolled back unless
    committed) after the response; `get_news_feed` / `get_npa_escalation` (with
    `HttpNpaGateway` on `settings.npa.npa_service_url`) take the `NewsRepo` from it, so one
    request = one session. Consumer: `build_consumer()` assembles the dedup/ranking
    repositories, model adapters, embedder, and the ordered pipeline stages once at
    process start, and hands them to `NewsIngestor` wrapped in the shared
    `common.core.rabbit.RabbitBatchConsumer[NewsDTO]` (bound with `NEWS_BINDING_KEY` =
    `news.raw.#`) — each consumed batch opens its own sessions inside the repositories
    it calls, not one shared session per batch.
  - `application/` — `ports/` (`NewsRepository`, `NpaGateway`, `DedupRepository`,
    `EventModels`, `NewsPipelineStage`, `RankingModels`, `RankingRepository`,
    `SummaryEmbedder` — grouped into `repositories/`/`gateways/`/`dedup/`/`ranking/`
    subpackages mirroring `infrastructure/`) + `dto/news/` (`NewsQuery` in, `NewsOut` out,
    now carrying `summary`/`event_cluster_id`) + `services/` (`NewsFeed`
    list/get/dismiss/restore, `NewsIngestor` checkpointed batch store, `NewsDeduplicator`,
    `NewsRanker`, `NpaEscalation` flag + register act) + `errors/`.
  - `domain/` — pure entities and rules, one package per entity: `event_summary/`,
    `event_cluster/`, `company_profile/`.
  - `infrastructure/` — `repositories/` (`NewsRepo` over the session it is given for the
    read API — writes stage, `commit()` persists; `SqlDedupRepository` /
    `SqlRankingRepository`, a fresh session per call, for the consumer pipeline),
    `dedup/` + `ranking/` (OpenRouter models, the packaged GS Labs profile, local
    embeddings), and `gateways/` (`HttpNpaGateway` → `npa_service`). No rabbit code here —
    the batching consumer is the shared one in `common/core/rabbit/`.
  - `api/routes/` — FastAPI routers only: `news.py` (`GET /`, `GET /{id}`,
    `POST /{id}/dismiss`, `POST /{id}/restore`, `POST /{id}/npa`), `health.py`.

Each unseen URL passes through batched primary-event extraction and a persisted per-news
summary; the same call judges whether the item reports a Russian normative act (bill, law,
decree, regulator's requirement) that concerns the company and calls for action — if so the
row is stored with `is_alert = true`, the flag manual escalation also sets. The summary
checkpoint is committed before embedding (OpenRouter Embeddings API); the whole prepared batch
is then retrieved against the HNSW cosine index and conservatively aligned to candidate event
clusters. Each affected cluster is ranked as one object and upserted once into
`news_cluster_ranking`. A retry resumes without repeating completed summary or dedup checkpoints.

Notes: batching (in `common.core.rabbit`) = `prefetch_count == NEWS_BATCH_SIZE` (100)
+ a flush every `NEWS_BATCH_INTERVAL_SECONDS` (60) **or** when the buffer is full,
whichever first — the batch acks only once every stage (summary, embedding, dedup,
ranking) has committed its own checkpoint; nack on `BatchStoreError` (`NewsStoreError`
from a repository write, or `NewsProcessingError` wrapping a model/embedding failure) —
requeued while `NEWS_REQUEUE_ON_STORE_ERROR`
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
