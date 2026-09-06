"""Conflict raised when the NPA service already stores a news URL."""

from news_service.application.errors.npa_gateway_error import NpaGatewayError


class NpaConflictError(NpaGatewayError):
    """The NPA service already holds an act with this URL."""

    def __init__(self, url: str) -> None:
        super().__init__(f"npa already exists: url={url}")
        self.url = url
