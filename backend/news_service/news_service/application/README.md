# application

Use-case / orchestration layer. Coordinates via **ports** (interfaces it defines and
infrastructure implements); depends on the shared `domain` package (schemas +
entities), never on concrete infra. Collaborators are injected by the composition
root (`deps.py`).

- `ports/` — the interfaces (Protocols): `NewsRepository` (data access) and
  `NewsBatchHandler` (the shared `domain.core.rabbit.BatchHandler` narrowed to
  `NewsDTO` — what the bus consumer hands a batch to).
- `dto/` — the response DTO (Pydantic) for the read API.
- `services/` — `NewsFeed` (list / dismiss) and `NewsIngestor` (batch ingest, implements
  `NewsBatchHandler`), one class per module.
- `errors.py` — `NewsStoreError` (subclasses `BatchStoreError`: a batch write failed;
  the shared consumer requeues).

Notes: import ports (`application.ports`), not infra classes. `NewsBatchHandler` is
unusual in pointing *inward* — infrastructure (the consumer) calls it, application
implements it — which is exactly how a message-driven entry point plugs into the onion.
