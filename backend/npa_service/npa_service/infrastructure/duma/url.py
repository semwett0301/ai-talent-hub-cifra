"""Strict allow-list validation for State Duma bill and download URLs."""

import re
from urllib.parse import urlsplit

from npa_service.application.errors import InvalidNpaUrlError

DUMA_HOST = "sozd.duma.gov.ru"
_BILL_PATH = re.compile(r"^/bill/(?P<number>\d+-\d+)/?$")


def normalize_duma_bill_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    match = _BILL_PATH.fullmatch(parsed.path)
    if not _is_allowed(parsed) or match is None or parsed.query or parsed.fragment:
        raise InvalidNpaUrlError("expected https://sozd.duma.gov.ru/bill/<number>")
    return f"https://{DUMA_HOST}/bill/{match.group('number')}"


def validate_duma_download_url(url: str) -> None:
    parsed = urlsplit(url)
    is_document_path = parsed.path.startswith(("/download/", "/s3files/"))
    if not _is_allowed(parsed) or not is_document_path:
        raise InvalidNpaUrlError("State Duma download redirected outside the allowed host")


def _is_allowed(parsed) -> bool:
    return (
        parsed.scheme == "https"
        and parsed.hostname == DUMA_HOST
        and parsed.port is None
        and not parsed.username
        and not parsed.password
    )
