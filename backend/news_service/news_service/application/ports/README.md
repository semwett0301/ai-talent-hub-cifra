# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). Re-exported from `__init__.py`.

- `repositories.py` — `NewsRepository`: `list_all(limit, offset)`, `mark_alert(id)`
  (sets `is_alert = true`, None when the id is unknown), and `add_many` — the batch
  insert the consumer path uses (one transaction, duplicates by `url` skipped,
  returns the inserted count; raises `NewsStoreError` on failure).
- `ingest.py` — `NewsBatchHandler` (`handle_batch`): the inward-facing port the bus
  consumer calls with one batch of `NewsDTO`s. Implemented by `NewsIngestor`
  (application), consumed by `RabbitNewsConsumer` (infrastructure).

Notes: ports reference `domain.schemas.News` and the shared
`domain.entities.news.NewsDTO` contract directly. `add_many` / `handle_batch` **raise**
`NewsStoreError` rather than returning a sentinel — the consumer needs a hard signal to
requeue the whole batch, and a count of `0` legitimately means "all duplicates".
