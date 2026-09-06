"""Temporary State Duma transport failure."""

from npa_service.application.errors.npa_source_error import NpaSourceError


class NpaSourceUnavailableError(NpaSourceError):
    """The State Duma endpoint was unavailable or returned an HTTP error."""
