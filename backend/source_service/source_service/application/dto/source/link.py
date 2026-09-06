"""`SourceLink` — a client-supplied source address, validated at the API boundary."""

from typing import Annotated

from pydantic import AfterValidator

from source_service.application.parse import is_telegram_link
from source_service.domain.urls import normalize_url

LINK_ERROR = "link must be an http(s) URL, e.g. https://example.com"


def _supported_link(link: str) -> str:
    if not normalize_url(link) and not is_telegram_link(link):
        raise ValueError(LINK_ERROR)

    return link


SourceLink = Annotated[str, AfterValidator(_supported_link)]
