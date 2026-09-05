"""Shared RabbitMQ batch consuming — the mechanism every bus consumer service reuses.

A service supplies the message model (a pydantic class), a `BatchHandler` for that
model, and a `BatchConsumerConfig` (both in `model/`); `RabbitBatchConsumer` (in
`consumer/`) does the rest: prefetch, buffer-and-ack-later batching, requeue (or drop,
per config) on `BatchStoreError` (from `common.core.errors`).
"""

from common.core.rabbit.consumer import MessageBatch, RabbitBatchConsumer
from common.core.rabbit.model import BatchConsumerConfig, BatchHandler

__all__ = [
    "BatchConsumerConfig",
    "BatchHandler",
    "MessageBatch",
    "RabbitBatchConsumer",
]
