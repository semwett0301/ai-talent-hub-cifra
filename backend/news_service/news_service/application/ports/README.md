# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). Re-exported from `__init__.py`.

- `repositories.py` — `NewsRepository`: data access over **one unit of work** (a request,
  a batch — scoped by `deps.py`, never by the use case). Reads: `list_page(query)` /
  `count(query)` (the page a `NewsQuery` asks for and how many rows match its filters),
  `get(id)`. Writes *stage* and return the row (None when the id is unknown):
  `add_many(items)` (the batch insert — duplicates by `url` and items whose source is gone
  are skipped, returns the inserted count), `mark_alert(id)`, `mark_dismissed(id)`,
  `mark_restored(id)`. `commit()` persists everything staged; a unit of work that ends
  without it rolls back. `add_many` / `commit` raise `NewsStoreError` on a DB failure.
- `npa_gateway.py` — `NpaGateway`: `create(NpaDTO) -> id` registers an act in
  `npa_service`; raises `NpaConflictError` (409 there) or `NpaGatewayError` (anything
  else) instead of returning a sentinel, so the use case can stop before `commit()`.
- `batch_handler.py` — `NewsBatchHandler`: the shared `common.core.rabbit.BatchHandler`
  narrowed to `NewsDTO` — the inward-facing port the bus consumer calls with one
  batch. Implemented by `NewsIngestor` (application) and wrapped per batch by
  `deps.BatchScope`, consumed by the shared `RabbitBatchConsumer` (`common`).

Notes: the use case decides **when** to commit — after every step that has to succeed
first (an external call, a whole batch) has succeeded — and knows nothing about sessions.
Ports reference `common.schemas.News` and the shared `common.entities.news.NewsDTO`
contract directly. `add_many` / `handle_batch` **raise** `NewsStoreError` (a
`BatchStoreError`) rather than returning a sentinel — the consumer needs a hard signal to
requeue the whole batch, and a count of `0` legitimately means "all duplicates".
