# application

Use-case / orchestration layer. Coordinates via **ports** (interfaces it defines and
infrastructure implements); depends on the shared `common` package (schemas +
entities), never on concrete infra. Collaborators are injected by the composition
root (`deps.py`).

- `ports/` — the interfaces (Protocols): `NewsRepository` (data access over one unit of
  work: writes stage, `commit()` persists), `NewsBatchHandler` (the shared
  `common.core.rabbit.BatchHandler` narrowed to `NewsDTO` — what the bus consumer hands
  a batch to), and `NpaGateway` (the outbound call to `npa_service`).
- `dto/` — the response DTO (Pydantic) for the read API.
- `services/` — `NewsFeed` (list / dismiss), `NewsIngestor` (batch ingest, implements
  `NewsBatchHandler`), and `NpaEscalation` (dismiss + register an act, atomically), one
  class per module.
- `errors.py` — `NewsStoreError` (subclasses `BatchStoreError`: a batch write failed;
  the shared consumer nacks it — requeue by default, `NEWS_REQUEUE_ON_STORE_ERROR`);
  `NpaGatewayError` / `NpaConflictError` (npa_service did not confirm the act / already
  has that `url`) — the API maps them to 502 / 409.

Notes: import ports (`application.ports`), not infra classes. `NewsBatchHandler` is
unusual in pointing *inward* — infrastructure (the consumer) calls it, application
implements it — which is exactly how a message-driven entry point plugs into the onion.
`NpaGateway` is the one *outbound* integration: the use case owns the "dismiss only if
the act was accepted" rule, the gateway only speaks HTTP.
