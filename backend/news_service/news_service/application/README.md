# application

Use-case / orchestration layer. Coordinates via **ports** (interfaces it defines and
infrastructure implements); depends on the shared `common` package (schemas +
entities), never on concrete infra. Collaborators are injected by the composition
root (`deps.py`).

- `ports/` — the interfaces (Protocols), grouped into subpackages mirroring
  `infrastructure/` (`repositories/`, `dedup/`, `ranking/`, `gateways/`): `NewsRepository`
  (data access over one unit of work: writes stage, `commit()` persists), `NpaGateway`
  (the outbound call to `npa_service`), and the consumer pipeline's own ports:
  `DedupRepository`, `RankingRepository`, `EventModels`, `RankingModels`,
  `SummaryEmbedder`. `NewsPipelineStage` stays at the root (no infra-side counterpart).
  There is no news-specific batch-handler port — `NewsIngestor` implements the shared
  `common.core.rabbit.BatchHandler[NewsDTO]` directly.
- `dto/` — the response DTO (Pydantic) for the read API.
- `services/` — `NewsFeed` (list / dismiss), `NewsIngestor` (staged batch ingest),
  `NewsDeduplicator` (same-event clustering), `NewsRanker` (one result per cluster), and
  `NpaEscalation` (dismiss + register an act atomically), one class per module.
- `errors/` — persistence/model/embedding errors mapped to `BatchStoreError` so the
  shared consumer nacks and retries the batch;
  `NpaGatewayError` / `NpaConflictError` (npa_service did not confirm the act / already
  has that `url`) — the API maps them to 502 / 409.

Notes: import ports (`application.ports`), not infra classes. `NewsIngestor`'s conformance
to the shared `BatchHandler[NewsDTO]` is unusual in pointing *inward* — infrastructure
(the consumer) calls it, application implements it — which is exactly how a
message-driven entry point plugs into the onion; unlike the other ports here, no
news-specific narrowing exists for it; nothing else in the service depends on it, so the
shared kernel's own contract (and its docstring) is the only one needed. `NpaGateway` is
the one *outbound* integration: the use case owns the "dismiss only if the act was
accepted" rule, the gateway only speaks HTTP.
