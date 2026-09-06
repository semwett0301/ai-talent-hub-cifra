"""Application errors — raised by use cases / repositories, mapped by the outer layers."""

from common.core.errors import BatchStoreError


class NewsStoreError(BatchStoreError):
    """A news write or its commit failed; on the consumer path the batch is nacked (requeue by default)."""


class NpaGatewayError(RuntimeError):
    """`npa_service` did not confirm the act — unreachable, timed out, or replied non-2xx."""


class NpaConflictError(NpaGatewayError):
    """`npa_service` already holds an act with this `url` (it replied 409)."""

    def __init__(self, url: str) -> None:
        super().__init__(f"npa already exists: url={url}")
        self.url = url
