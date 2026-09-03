# infrastructure

Implementations of the application ports plus adapters to the outside world (DB,
message bus, external sources). Depends on `application` (the ports) and `domain`;
nothing depends inward on it except the composition root (`deps.py`).

- `persistence/` — ORM schemas (tables) + repositories over them.
- `rabbit/` — `RabbitConnector`, the `NewsPublisher` implementation.
- `collectors/` — `Pull`/`PushCollector` implementations (RSS, Web, Telegram).

Notes: classes here structurally satisfy the ports (no need to import them); `deps.py`
constructs them and injects them where a port is expected. DB engine/session come
from `common.core.session`.
