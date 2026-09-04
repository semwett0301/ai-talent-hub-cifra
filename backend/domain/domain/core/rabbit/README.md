# domain.core.rabbit

The shared **batching consumer** for RabbitMQ topic exchanges. Any service that needs
to consume a stream of pydantic messages and persist them in batches reuses this
instead of writing its own consumer; the service contributes only the message model,
a `BatchHandler`, and a config. One class per module, re-exported from `__init__.py`.

- `consumer.py` — `RabbitBatchConsumer[T]`: connects (`connect_robust`), declares the
  topic exchange + a durable queue bound with `config.binding_key`, sets
  `prefetch_count` = batch size, and consumes. Deliveries are buffered **unacked**; a
  flusher task wakes when the buffer is full **or** the interval elapses
  (`asyncio.Event` + `wait_for`), hands the parsed batch to the `BatchHandler`, then
  acks the whole run. On `BatchStoreError` the run is nacked back (requeue) and the
  loop sleeps one interval. `start`/`stop` lifecycle driven by the service's
  lifespan; `stop` drains the buffer first.
- `batch.py` — `MessageBatch[T]`: one flush's deliveries. Parses each body into the
  given `model` (unparseable → `reject(requeue=False)`, WARNING) and settles the run
  in one frame via `ack(multiple=True)` / `nack(multiple=True, requeue=True)` on the
  last valid delivery. Settle failures (channel reset) are logged, not raised — the
  broker redelivers, and the handler must be idempotent anyway.
- `handler.py` — `BatchHandler[T]` (Protocol): `handle_batch(items) -> int`. The
  inward-facing port: the service's application layer **implements** it (inherit the
  Protocol), the consumer calls it.
- `config.py` — `BatchConsumerConfig`: frozen dataclass of the connection + batching
  knobs (`url`, `exchange_name`, `queue_name`, `binding_key`, `batch_size`,
  `batch_interval_seconds`), filled from `settings` in the service's `deps.py`.
- `errors.py` — `BatchStoreError`: raise (or subclass) it from the handler to have the
  batch requeued; anything else is a bug and propagates.

Notes: why buffer-and-ack-later rather than `basic.get` polling — AMQP has no
"give me N" call; `basic.get` is a round trip per message the broker docs discourage,
while `consume` + prefetch streams messages and the deferred ack is what turns them
into a batch with at-least-once semantics. `prefetch_count == batch_size` means the
buffer can never exceed one batch, so memory is bounded without extra bookkeeping.
Wiring example: `news_service/deps.py` (`RabbitBatchConsumer(config, NewsIngestor(...), NewsDTO)`).
