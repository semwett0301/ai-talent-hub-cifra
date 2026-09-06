# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). Re-exported from `__init__.py`.

- `repositories.py` — `NewsRepository`: data access over **one unit of work** (one HTTP
  request — scoped by `deps.py`, never by the use case). Reads: `list_matching(query)`
  (every row a `NewsQuery`'s filters admit, newest publication first), `get(id)`. Writes
  *stage* and return the row (None when the id is unknown): `mark_alert(id)`,
  `mark_dismissed(id)`, `mark_restored(id)`. `commit()` persists everything staged; a
  unit of work that ends without it rolls back. `commit()` raises `NewsStoreError` on a
  DB failure. The consumer's own write path — checkpointed ingestion, dedup, ranking —
  goes through `DedupRepository` / `RankingRepository` instead, not this port.
- `dedup_repository.py` — idempotent summarized-news writes, pending work, pgvector
  candidates, and final cluster assignments.
- `event_models.py` — batched extraction/summary and precluster-alignment LLM stages.
- `summary_embedder.py` — local summary embedding contract.
- `pipeline_stage.py` — ordered post-summary stage contract used by dedup and ranking.
- `ranking_models.py` — cluster impact/urgency and semantic reranker model boundary.
- `ranking_repository.py` — affected-cluster loading and ranking upsert boundary.
- `npa_gateway.py` — `NpaGateway`: `create(NpaDTO) -> id` registers an act in
  `npa_service`; raises `NpaConflictError` (409 there) or `NpaGatewayError` (anything
  else) instead of returning a sentinel, so the use case can stop before `commit()`.
- `batch_handler.py` — `NewsBatchHandler`: the shared `common.core.rabbit.BatchHandler`
  narrowed to `NewsDTO` — the inward-facing port the bus consumer calls with one
  batch. Implemented by `NewsIngestor` (application), assembled once by
  `deps.build_consumer()`, consumed by the shared `RabbitBatchConsumer` (`common`).

Notes: the use case decides **when** to commit — after every step that has to succeed
first (an external call, a whole batch) has succeeded — and knows nothing about sessions.
Ports reference `common.schemas.News` and the shared `common.entities.news.NewsDTO`
contract directly. `commit()` / `handle_batch` **raise** `NewsStoreError` (a
`BatchStoreError`) rather than returning a sentinel — the consumer needs a hard signal to
requeue the whole batch. Persistence and model implementations on the consumer side wrap
failures in a `BatchStoreError` subclass the same way, so the whole batch is requeued.
