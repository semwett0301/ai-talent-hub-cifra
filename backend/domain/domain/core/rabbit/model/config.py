"""BatchConsumerConfig — the connection + batching knobs `RabbitBatchConsumer` takes."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BatchConsumerConfig:
    url: str
    exchange_name: str
    queue_name: str
    # Topic pattern the queue is bound with (e.g. `news.raw.#`).
    binding_key: str
    # A batch flushes when it holds `batch_size` messages or `batch_interval_seconds`
    # elapsed since the previous flush — whichever comes first. `batch_size` is also
    # the channel prefetch, so the broker never hands out more than one batch unacked.
    batch_size: int
    batch_interval_seconds: float
    # What happens to a batch the handler could not store (`BatchStoreError`): `True`
    # nacks it back onto the queue for another attempt (at-least-once), `False` drops it.
    requeue_on_store_error: bool
