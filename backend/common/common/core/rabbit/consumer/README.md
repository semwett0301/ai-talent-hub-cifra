# common.core.rabbit.consumer

The **implementation** side of the shared batch consumer — the aio-pika code that turns
a stream of deliveries into batches for a `BatchHandler` (definitions in `../model`).

- `batch_consumer.py` — `RabbitBatchConsumer[T]`: connects (`connect_robust`),
  declares the topic exchange + a durable queue bound with `config.binding_key`, sets
  `prefetch_count` = batch size, and consumes. The consume callback only drops each
  delivery into an inbox (`asyncio.Queue`); a single **runner task** is the inbox's
  only reader: it waits for the first delivery, then collects more until the batch is
  full **or** the interval since that first delivery elapsed (`asyncio.timeout_at`),
  hands the parsed batch to the `BatchHandler`, then acks the whole run. On
  `BatchStoreError` the run is nacked — requeued when `config.requeue_on_store_error`
  is set, dropped otherwise — and the runner backs off one interval; the WARNING names
  the error and its whole `raise ... from` chain (`store failed: A <- B <- C`), so the
  root cause (an LLM 402, a missing column) is readable without a traceback. `start`/`stop`
  lifecycle driven by the service's lifespan; `stop` cancels the consumer, then the
  runner, which drains the collected + inboxed deliveries before exiting.
- `message_batch.py` — `MessageBatch[T]`: one flush's deliveries. Parses each body into
  the given `model` (unparseable → `reject(requeue=False)`, WARNING) and settles the run
  in one frame via `ack` / `requeue` / `drop` (`ack` or `nack(requeue=True|False)`, all
  `multiple=True`) on the last valid delivery. Settle failures (channel reset) are
  logged, not raised — the broker redelivers, and the handler must be idempotent anyway.

Notes: `batch_consumer` imports `message_batch` directly (sibling module), and the
definitions via the `..model` package. One task owns the buffer, so there is no
`Event`/`Lock`: callback and runner meet only at the inbox, and `ack(multiple=True)`
can never overlap another run. The runner uses its own `asyncio.Queue` rather than
aio-pika's `queue.iterator()` on purpose — `QueueIterator.__anext__` **closes the
iterator** when its wait is cancelled, so it cannot be wrapped in a timeout; cancelling
`asyncio.Queue.get()` is safe. Latency of a delivery is therefore bounded by one
interval from *its own* batch's first message, and an idle queue runs no timers.
