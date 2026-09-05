"""Application errors — raised by use cases / repositories, mapped by the outer layers."""

from domain.core.errors import BatchStoreError


class NewsStoreError(BatchStoreError):
    """A news batch could not be written; the shared consumer nacks it (requeue by default)."""


class NpaGatewayError(RuntimeError):
    """`npa_service` did not confirm the act — unreachable, timed out, or replied non-2xx."""


class NpaConflictError(NpaGatewayError):
    """`npa_service` already holds an act with this `url` (it replied 409)."""

    def __init__(self, url: str) -> None:
        super().__init__(f"npa already exists: url={url}")
        self.url = url
