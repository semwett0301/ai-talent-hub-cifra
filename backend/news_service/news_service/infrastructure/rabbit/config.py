"""RabbitConsumerConfig — the connection + batching knobs `RabbitNewsConsumer` takes."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RabbitConsumerConfig:
    url: str
    exchange_name: str
    queue_name: str
    # A batch flushes when it holds `batch_size` messages or `batch_interval_seconds`
    # elapsed since the previous flush — whichever comes first. `batch_size` is also
    # the channel prefetch, so the broker never hands out more than one batch unacked.
    batch_size: int
    batch_interval_seconds: float
