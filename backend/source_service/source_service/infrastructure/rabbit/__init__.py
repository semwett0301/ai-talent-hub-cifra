"""RabbitMQ infrastructure — the connector that publishes collected news."""

from source_service.infrastructure.rabbit.connector import RabbitConnector

__all__ = ["RabbitConnector"]
