"""Ports — interfaces application depends on, implemented in infrastructure or application."""

from news_service.application.ports.batch_handler import NewsBatchHandler
from news_service.application.ports.npa_gateway import NpaGateway
from news_service.application.ports.repositories import NewsRepository
from news_service.application.ports.transaction import NewsTransaction

__all__ = ["NewsBatchHandler", "NewsRepository", "NewsTransaction", "NpaGateway"]
