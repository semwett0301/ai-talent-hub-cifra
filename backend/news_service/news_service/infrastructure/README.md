# infrastructure

Implementations of the application ports plus adapters to the outside world (DB,
message bus). Depends on `application` (the ports) and `domain`; nothing depends
inward on it except the composition root (`deps.py`).

- `repositories/` — `NewsRepo` over the ORM, a session per call (the `News` table
  itself lives in `domain/schemas/`); `add_many` is the one-statement batch insert.
- `rabbit/` — `RabbitNewsConsumer` (+ `MessageBatch`, `RabbitConsumerConfig`): the
  batching consumer that calls the `NewsBatchHandler` port.

Notes: classes here implement the ports (they inherit the `Protocol`); `deps.py`
constructs them and injects them where a port is expected. DB engine/session come
from `domain.core.session`.
