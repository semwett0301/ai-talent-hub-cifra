# news_service (package)

The importable service package. The service itself is described in `../README.md`; this
file only maps the layers.

- `main.py` — FastAPI app + lifespan (start the shared RabbitMQ batch consumer).
- `deps.py` — composition root: builds the consumer, the ingestor and the repository.
- `application/` — use cases and ports: `services/` (`NewsIngestor`), `ports/`
  (`NewsBatchHandler`, `NewsRepository`), `dto/`.
- `infrastructure/` — port implementations: `repositories/` (`NewsRepo`, one-statement
  batch insert, unique on `url`).
- `api/` — FastAPI routers (`/news` list + dismiss).

Notes: the bus is the entry point — `common.core.rabbit.RabbitBatchConsumer` calls the
inward-facing `NewsBatchHandler`; the consumer mechanism itself lives in `common`.
