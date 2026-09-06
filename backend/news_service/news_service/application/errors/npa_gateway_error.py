"""Failure raised when the NPA service does not accept a request."""


class NpaGatewayError(RuntimeError):
    """The NPA service was unreachable, timed out, or returned a non-success response."""
