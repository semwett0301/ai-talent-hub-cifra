"""State Duma response did not contain a usable bill card."""

from npa_service.application.errors.npa_source_error import NpaSourceError


class InvalidNpaPageError(NpaSourceError):
    """The page is not a bill card or has no supported Word bill text."""
