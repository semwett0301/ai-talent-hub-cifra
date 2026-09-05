# infrastructure

Implementations of the application ports plus adapters to the outside world (DB,
message bus). Depends on `application` (the ports) and `domain`; nothing depends
inward on it except the composition root (`deps.py`).

- `repositories/` — `NewsRepo` over the ORM, a session per call (the `News` table
  itself lives in `domain/schemas/`); `add_many` is the one-statement batch insert;
  `SqlNewsTransaction` is the held-open unit of work `begin()` returns.
- `gateways/` — `HttpNpaGateway`: the `NpaGateway` port over httpx, POSTing acts to
  `npa_service` (`settings.npa_service_url`).

The RabbitMQ consumer is **not** here: it is the shared `domain.core.rabbit.
RabbitBatchConsumer`, instantiated in `deps.py` with `NewsDTO` and `NewsIngestor`.

Notes: classes here implement the ports (they inherit the `Protocol`); `deps.py`
constructs them and injects them where a port is expected. DB engine/session come
from `domain.core.db`.
