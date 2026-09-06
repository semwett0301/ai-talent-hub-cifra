# application

Use-case / orchestration layer. Coordinates via **ports** (interfaces it defines and
infrastructure implements); depends on the shared `common` package (schemas +
entities), never on concrete infra. Collaborators are injected by the composition
root (`deps.py`).

- `ports/` — repository, event-model, embedding, batch-handler, transaction, and NPA
  gateway protocols.
- `dto/` — the response DTO (Pydantic) for the read API.
- `services/` — `NewsFeed` (list / dismiss), `NewsIngestor` (staged batch ingest),
  `NewsDeduplicator` (same-event clustering), and `NpaEscalation` (dismiss + register an
  act, atomically), one class per module.
- `errors/` — persistence/model/embedding errors mapped to `BatchStoreError` so the
  shared consumer nacks and retries the batch;
  `NpaGatewayError` / `NpaConflictError` (npa_service did not confirm the act / already
  has that `url`) — the API maps them to 502 / 409.

Notes: import ports (`application.ports`), not infra classes. `NewsBatchHandler` is
unusual in pointing *inward* — infrastructure (the consumer) calls it, application
implements it — which is exactly how a message-driven entry point plugs into the onion.
`NpaGateway` is the one *outbound* integration: the use case owns the "dismiss only if
the act was accepted" rule, the gateway only speaks HTTP.
