# infrastructure

Implementations of the application ports plus adapters to the outside world (DB,
message bus). Depends on `application` (the ports) and `common`; nothing depends
inward on it except the composition root (`deps.py`).

- `repositories/` — `NewsRepo` for the read side, `SqlDedupRepository` for summarized
  ingestion/pgvector clustering, and `SqlNewsTransaction` for held-open API mutations.
- `dedup/` — OpenRouter structured model stages, local CPU embeddings, and prompts.
- `gateways/` — `HttpNpaGateway`: the `NpaGateway` port over httpx, POSTing acts to
  `npa_service` (`settings.npa.npa_service_url`).

The RabbitMQ consumer is **not** here: it is the shared `common.core.rabbit.
RabbitBatchConsumer`, instantiated in `deps.py` with `NewsDTO` and `NewsIngestor`.

Notes: classes here implement the ports (they inherit the `Protocol`); `deps.py`
constructs them and injects them where a port is expected. DB engine/session come
from `common.core.db`.
