"""Implementation of the shared batch consumer over aio-pika."""

from domain.core.rabbit.consumer.batch_consumer import RabbitBatchConsumer
from domain.core.rabbit.consumer.message_batch import MessageBatch

__all__ = ["MessageBatch", "RabbitBatchConsumer"]
