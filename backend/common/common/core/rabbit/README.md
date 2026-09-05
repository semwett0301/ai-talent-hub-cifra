# common.core.rabbit

The shared **batching consumer** for RabbitMQ topic exchanges. Any service that needs
to consume a stream of pydantic messages and persist them in batches reuses this
instead of writing its own consumer; the service contributes only the message model,
a `BatchHandler`, and a config. Split into definitions and implementation, both
re-exported from `__init__.py` — import from `common.core.rabbit`.

- `model/` — **definitions** a service touches: `BatchConsumerConfig` (the knobs) and
  `BatchHandler[T]` (the port the service implements). No I/O.
- `consumer/` — **implementation**: `RabbitBatchConsumer[T]` (connect, prefetch,
  buffer, flush, ack/nack) and its helper `MessageBatch[T]` (parse + settle one run).

The failure signal itself, `BatchStoreError`, is not rabbit-specific and lives in
`common.core.errors`: raise (or subclass) it from the handler to have the batch nacked
(requeued or dropped per config); anything else is a bug and propagates.

Notes: why buffer-and-ack-later rather than `basic.get` polling — AMQP has no
"give me N" call; `basic.get` is a round trip per message the broker docs discourage,
while `consume` + prefetch streams messages and the deferred ack is what turns them
into a batch with at-least-once semantics. `prefetch_count == batch_size` means the
inbox can never hold more than one batch, so memory is bounded without extra
bookkeeping. The batch window starts at its first delivery, so a message waits at most
one interval and an idle queue costs nothing.
Wiring example: `news_service/deps.py` (`RabbitBatchConsumer(config, NewsIngestor(...), NewsDTO)`).
