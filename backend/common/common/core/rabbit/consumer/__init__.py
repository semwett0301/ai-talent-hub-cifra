"""Implementation of the shared batch consumer over aio-pika."""

from common.core.rabbit.consumer.batch_consumer import RabbitBatchConsumer
from common.core.rabbit.consumer.message_batch import MessageBatch

__all__ = ["MessageBatch", "RabbitBatchConsumer"]
