# news_service (package)

The importable service package. The service itself is described in `../README.md`; this
file only maps the layers.

- `main.py` — FastAPI app + lifespan (start the shared RabbitMQ batch consumer).
- `deps.py` — composition root: builds the consumer, repositories, model adapters,
  embedder, and use cases.
- `application/` — use cases and ports for ingestion, deduplication, ranking, feed,
  and escalation.
- `domain/` — event dedup and company-relevance entities and pure rules.
- `infrastructure/` — read, dedup, and ranking repositories plus OpenRouter, profile,
  and local embedding implementations.
- `api/` — FastAPI routers (`/news` list + dismiss).

Notes: the bus is the entry point — `common.core.rabbit.RabbitBatchConsumer` calls the
inward-facing `NewsBatchHandler`; the consumer mechanism itself lives in `common`.
