# news_service (package)

The importable service package. The service itself is described in `../README.md`; this
file only maps the layers.

- `main.py` — FastAPI app + lifespan (start the shared RabbitMQ batch consumer).
- `deps.py` — composition root: builds the consumer, repositories, event models, embedder,
  and use cases.
- `application/` — use cases and ports for ingestion, deduplication, feed, and escalation.
- `domain/dedup/` — event summaries, candidates, decisions, and fail-closed policy.
- `infrastructure/` — read and dedup repositories plus OpenRouter and local embedding
  implementations.
- `api/` — FastAPI routers (`/news` list + dismiss).

Notes: the bus is the entry point — `common.core.rabbit.RabbitBatchConsumer` calls the
inward-facing `NewsBatchHandler`; the consumer mechanism itself lives in `common`.
