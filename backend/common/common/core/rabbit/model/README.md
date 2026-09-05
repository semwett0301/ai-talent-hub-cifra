# common.core.rabbit.model

The **definitions** side of the shared batch consumer — what a service supplies and
implements. No I/O, no aio-pika; the implementation lives in `../consumer`.

- `config.py` — `BatchConsumerConfig`: frozen dataclass of the connection + batching
  knobs (`url`, `exchange_name`, `queue_name`, `binding_key`, `batch_size`,
  `batch_interval_seconds`, `requeue_on_store_error`), filled from `settings` in the
  service's `deps.py`.
- `handler.py` — `BatchHandler[T]` (Protocol): `handle_batch(items) -> int`. The
  inward-facing port: the service's application layer **implements** it (inherit the
  Protocol), the consumer calls it. Raises `BatchStoreError` (`common.core.errors`) to
  have the batch nacked.
