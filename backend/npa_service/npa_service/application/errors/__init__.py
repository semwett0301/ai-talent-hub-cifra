"""Application failures mapped at HTTP or scheduling boundaries."""

from npa_service.application.errors.change_model_error import ChangeModelError
from npa_service.application.errors.invalid_npa_page_error import InvalidNpaPageError
from npa_service.application.errors.invalid_npa_url_error import InvalidNpaUrlError
from npa_service.application.errors.npa_already_exists_error import NpaAlreadyExistsError
from npa_service.application.errors.npa_document_error import NpaDocumentError
from npa_service.application.errors.npa_source_error import NpaSourceError
from npa_service.application.errors.npa_source_unavailable_error import NpaSourceUnavailableError

__all__ = [
    "ChangeModelError",
    "InvalidNpaPageError",
    "InvalidNpaUrlError",
    "NpaAlreadyExistsError",
    "NpaDocumentError",
    "NpaSourceError",
    "NpaSourceUnavailableError",
]
