# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). Re-exported from `__init__.py`.

- `repositories.py` — `NewsRepository`: `list_all(limit, offset)`, `mark_alert(id)`
  (sets `is_alert = true` and commits, None when the id is unknown), `add_many` — the
  batch insert the consumer path uses (one transaction, duplicates by `url` skipped, a
  `source_id` whose source is gone stored as NULL, returns the inserted count; raises
  `NewsStoreError` on failure) — and `begin()`,
  which opens a `NewsTransaction`.
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

Notes: ports reference `common.schemas.News` and the shared
`common.entities.news.NewsDTO` contract directly. `add_many` / `handle_batch` **raise**
`NewsStoreError` (a `BatchStoreError`) rather than returning a sentinel — the consumer
needs a hard signal to requeue the whole batch, and a count of `0` legitimately means
"all duplicates".
