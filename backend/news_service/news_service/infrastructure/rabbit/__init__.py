"""RabbitMQ infrastructure — the batching consumer of the `news` exchange."""

from news_service.infrastructure.rabbit.config import RabbitConsumerConfig
from news_service.infrastructure.rabbit.consumer import RabbitNewsConsumer

__all__ = ["RabbitConsumerConfig", "RabbitNewsConsumer"]
