"""Base failure raised by the State Duma source adapter."""


class NpaSourceError(RuntimeError):
    """A remote page or document could not be retrieved or parsed."""
