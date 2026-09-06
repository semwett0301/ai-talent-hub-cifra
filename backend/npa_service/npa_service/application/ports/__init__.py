"""Ports — interfaces application depends on, implemented in infrastructure."""

from npa_service.application.ports.change_summarizer import ChangeSummarizer
from npa_service.application.ports.npa_source import NpaSource
from npa_service.application.ports.repositories import NpaRepository

__all__ = ["ChangeSummarizer", "NpaRepository", "NpaSource"]
