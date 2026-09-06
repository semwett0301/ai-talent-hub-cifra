# infrastructure

Implementations of the application ports plus adapters to the outside world (DB,
message bus). Depends on `application` (the ports) and `common`; nothing depends
inward on it except the composition root (`deps.py`).

- `repositories/` — read/transaction repositories plus summarized-news dedup and
  cluster-ranking persistence.
- `dedup/` — OpenRouter structured model stages, local CPU embeddings, and prompts.
- `ranking/` — GS Labs profile loading, structured impact assessment, and reranking.
- `gateways/` — `HttpNpaGateway`: the `NpaGateway` port over httpx, POSTing acts to
  `npa_service` (`settings.npa.npa_service_url`).

The RabbitMQ consumer is **not** here: it is the shared `common.core.rabbit.
RabbitBatchConsumer`, instantiated in `deps.py` with `NewsDTO` and `NewsIngestor`.

Notes: classes here implement the ports (they inherit the `Protocol`); `deps.py`
constructs them and injects them where a port is expected. DB engine/session come
from `common.core.db`.
