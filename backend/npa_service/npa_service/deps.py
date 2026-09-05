"""Composition root — wire infrastructure implementations into application.

The one place that knows every layer: it builds the concrete repository and hands
the application use case to it. Everything else depends only on ports.
"""

from npa_service.application.services import NpaCatalog
from npa_service.infrastructure.repositories import NpaRepo


def get_npa_catalog() -> NpaCatalog:
    """FastAPI use case. NpaRepo opens a session per call, so no request binding."""
    return NpaCatalog(NpaRepo())
