# rabbit

RabbitMQ consuming — the batching consumer of the `news` exchange (one class per
module, re-exported from `__init__.py`).

- `consumer.py` — `RabbitNewsConsumer`: connects (`connect_robust`), declares the
  topic exchange + a durable queue bound to `news.raw.#`, sets `prefetch_count` =
  batch size, and consumes. Deliveries are buffered **unacked**; a flusher task
  wakes when the buffer is full **or** the interval elapses (`asyncio.Event` +
  `wait_for`), hands the batch to the `NewsBatchHandler` port, then acks the whole
  run. On `NewsStoreError` the run is nacked back (requeue) and the loop sleeps one
  interval. `start`/`stop` lifecycle driven by `main.py`; `stop` drains the buffer.
- `batch.py` — `MessageBatch`: one flush's deliveries. Parses each body into a
  `NewsDTO` (unparseable → `reject(requeue=False)`, WARNING), and settles the run in
  one frame via `ack(multiple=True)` / `nack(multiple=True, requeue=True)` on the
  last valid delivery. Settle failures (channel reset) are logged, not raised — the
  broker redelivers and the unique `url` makes that harmless.
- `config.py` — `RabbitConsumerConfig`: frozen dataclass of the connection + batching
  knobs, filled from `settings` in `deps.py`.

Notes: why buffer-and-ack-later rather than `basic.get` polling — AMQP has no
"give me N" call; `basic.get` is a round trip per message the broker docs discourage,
while `consume` + prefetch streams messages and the deferred ack is what turns them
into a batch with at-least-once semantics. `prefetch_count == batch_size` means the
buffer can never exceed one batch, so memory is bounded without extra bookkeeping.
