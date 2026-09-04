# infrastructure

Implementations of the application ports plus adapters to the outside world (DB,
message bus, external sources). Depends on `application` (the ports) and `domain`;
nothing depends inward on it except the composition root (`deps.py`).

- `repositories/` — `SourceRepo` over the ORM, a session per call (the `Source`
  table itself lives in `domain/schemas/`).
- `rabbit/` — `RabbitConnector`, the `NewsPublisher` implementation.
- `collectors/` — `Pull`/`PushCollector` implementations (RSS, Web, Telegram).

Notes: classes here implement the ports (they inherit the `Protocol`); `deps.py`
constructs them and injects them where a port is expected. DB engine/session come
from `common.core.session`.
