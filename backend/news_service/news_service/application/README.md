# application

Use-case / orchestration layer. Coordinates via **ports** (interfaces it defines and
infrastructure implements); depends on the shared `domain` package (schemas +
entities), never on concrete infra. Collaborators are injected by the composition
root (`deps.py`).

- `ports/` — the interfaces (Protocols): `NewsRepository` (data access) and
  `NewsBatchHandler` (what the bus consumer hands a batch to).
- `dto/` — the response DTO (Pydantic) for the read API.
- `services/` — `NewsService` (list / dismiss) and `NewsIngestor` (batch ingest, implements
  `NewsBatchHandler`), one class per module.
- `errors.py` — `NewsStoreError` (a batch write failed; consumer requeues).

Notes: import ports (`application.ports`), not infra classes. `NewsBatchHandler` is
unusual in pointing *inward* — infrastructure (the consumer) calls it, application
implements it — which is exactly how a message-driven entry point plugs into the onion.
