# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). Re-exported from `__init__.py`.

- `repositories.py` — `NewsRepository`: read-side listing, alert mutation, and `begin()`.
- `dedup_repository.py` — idempotent summarized-news writes, pending work, pgvector
  candidates, and final cluster assignments.
- `event_models.py` — batched extraction/summary and precluster-alignment LLM stages.
- `summary_embedder.py` — local summary embedding contract.
- `pipeline_stage.py` — ordered post-summary stage contract used by dedup and ranking.
- `ranking_models.py` — cluster impact/urgency and semantic reranker model boundary.
- `ranking_repository.py` — affected-cluster loading and ranking upsert boundary.
- `transaction.py` — `NewsTransaction`: an async context manager over **one** DB
  transaction — `mark_alert(id)` *stages* the flip, `commit()` persists it, and leaving
  the block without a commit (or by exception) rolls it back. This is how a use case
  makes a DB change conditional on an external call.
- `npa_gateway.py` — `NpaGateway`: `create(NpaDTO) -> id` registers an act in
  `npa_service`; raises `NpaConflictError` (409 there) or `NpaGatewayError` (anything
  else) instead of returning a sentinel, so the transaction above can roll back.
- `batch_handler.py` — `NewsBatchHandler`: the shared `common.core.rabbit.BatchHandler`
  narrowed to `NewsDTO` — the inward-facing port the bus consumer calls with one
  batch. Implemented by `NewsIngestor` (application), consumed by the shared
  `RabbitBatchConsumer` (`common`).

Notes: persistence and model implementations wrap failures in a `BatchStoreError`
subclass before they reach the shared Rabbit consumer, so the whole batch is requeued.
