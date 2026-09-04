"""Ports — interfaces application depends on, implemented in infrastructure."""

from source_service.application.ports.collectors import PullCollector, PushCollector
from source_service.application.ports.publisher import NewsPublisher
from source_service.application.ports.registrar import SourceRegistrar
from source_service.application.ports.repositories import SourceRepository

__all__ = [
    "NewsPublisher",
    "PullCollector",
    "PushCollector",
    "SourceRegistrar",
    "SourceRepository",
]
