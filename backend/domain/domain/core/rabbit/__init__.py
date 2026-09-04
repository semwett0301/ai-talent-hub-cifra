"""Shared RabbitMQ batch consuming — the mechanism every bus consumer service reuses.

A service supplies the message model (a pydantic class), a `BatchHandler` for that
model, and a `BatchConsumerConfig`; `RabbitBatchConsumer` does the rest: prefetch,
buffer-and-ack-later batching, requeue on `BatchStoreError`.
"""

from domain.core.rabbit.batch import MessageBatch
from domain.core.rabbit.config import BatchConsumerConfig
from domain.core.rabbit.consumer import RabbitBatchConsumer
from domain.core.rabbit.errors import BatchStoreError
from domain.core.rabbit.handler import BatchHandler

__all__ = [
    "BatchConsumerConfig",
    "BatchHandler",
    "BatchStoreError",
    "MessageBatch",
    "RabbitBatchConsumer",
]
