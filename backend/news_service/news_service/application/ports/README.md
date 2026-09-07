# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). Re-exported from `__init__.py`.
Grouped the same way `infrastructure/` is — see each subpackage's own README:

- `repositories/` — `NewsRepository`, `DedupRepository`, `RankingRepository`. Mirrors
  `infrastructure/repositories/`.
- `dedup/` — `EventModels`, `SummaryEmbedder`. Mirrors `infrastructure/dedup/`.
- `ranking/` — `RankingModels`. Mirrors `infrastructure/ranking/`.
- `gateways/` — `NpaGateway`. Mirrors `infrastructure/gateways/`.
Two contracts intentionally do not live here — see the package docstring for why:
`NewsPipelineStage` sits inside `application/services/news_ingestor/` (both its
implementers and its sole consumer are nested there too, so it never crosses into
infrastructure).

No news-specific batch-handler port either: `NewsIngestor` (application) implements the shared
`common.core.rabbit.BatchHandler[NewsDTO]` directly — the inward-facing port the bus
consumer calls with one batch, assembled once by `deps.build_consumer()`, consumed by the
shared `RabbitBatchConsumer` (`common`). A narrowed local Protocol used to sit here; it
added nothing beyond a duplicate docstring and had exactly one implementer, so it was
removed.

Notes: the use case decides **when** to commit — after every step that has to succeed
first (an external call, a whole batch) has succeeded — and knows nothing about sessions.
Ports reference `common.schemas.News` and the shared `common.entities.news.NewsDTO`
contract directly. `commit()` / `handle_batch` **raise** `NewsStoreError` (a
`BatchStoreError`) rather than returning a sentinel — the consumer needs a hard signal to
requeue the whole batch. Persistence and model implementations on the consumer side wrap
failures in a `BatchStoreError` subclass the same way, so the whole batch is requeued.
