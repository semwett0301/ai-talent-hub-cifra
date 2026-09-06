"""Unsupported or corrupt bill text document error."""

from npa_service.application.errors.npa_source_error import NpaSourceError


class NpaDocumentError(NpaSourceError):
    """A selected Word document could not be converted to text."""
