# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). Re-exported from `__init__.py`.

- `repositories.py` — `NewsRepository`: `list_all(limit, offset)`, `mark_alert(id)`
  (sets `is_alert = true`, None when the id is unknown), and `add_many` — the batch
  insert the consumer path uses (one transaction, duplicates by `url` skipped,
  returns the inserted count; raises `NewsStoreError` on failure).
- `batch_handler.py` — `NewsBatchHandler`: the shared `common.core.rabbit.BatchHandler`
  narrowed to `NewsDTO` — the inward-facing port the bus consumer calls with one
  batch. Implemented by `NewsIngestor` (application), consumed by the shared
  `RabbitBatchConsumer` (common).

Notes: ports reference `common.schemas.News` and the shared
`common.entities.news.NewsDTO` contract directly. `add_many` / `handle_batch` **raise**
`NewsStoreError` (a `BatchStoreError`) rather than returning a sentinel — the consumer
needs a hard signal to requeue the whole batch, and a count of `0` legitimately means
"all duplicates".
