"""Async allow-listed client for State Duma bill cards and Word files."""

import httpx
from common.core.logging import get_logger

from npa_service.application.errors import InvalidNpaPageError, NpaSourceUnavailableError
from npa_service.application.ports import NpaSource
from npa_service.domain import BillSnapshot
from npa_service.infrastructure.duma.docx_parser import DocxParser
from npa_service.infrastructure.duma.page_parser import DumaPageParser
from npa_service.infrastructure.duma.url import (
    normalize_duma_bill_url,
    validate_duma_download_url,
)

logger = get_logger(__name__)


async def _read_limited(response: httpx.Response, max_bytes: int) -> bytes:
    content = bytearray()
    async for chunk in response.aiter_bytes():
        content.extend(chunk)
        if len(content) > max_bytes:
            raise ValueError(f"State Duma response exceeds {max_bytes} bytes")
    return bytes(content)


def _validate_final_url(final_url: str, requested_url: str) -> None:
    if "/download/" in requested_url:
        validate_duma_download_url(final_url)
        return
    if normalize_duma_bill_url(final_url) != normalize_duma_bill_url(requested_url):
        raise ValueError("State Duma bill redirected to another card")


def _decode_page(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InvalidNpaPageError("State Duma bill page is not valid UTF-8") from error


class DumaClient(NpaSource):
    def __init__(self, timeout_seconds: float, max_document_bytes: int, user_agent: str) -> None:
        self.__client = httpx.AsyncClient(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": user_agent},
        )
        self.__max_document_bytes = max_document_bytes
        self.__page_parser = DumaPageParser()
        self.__docx_parser = DocxParser()

    async def fetch(self, url: str) -> BillSnapshot:
        canonical_url = normalize_duma_bill_url(url)
        logger.info("duma bill fetch started: url=%s", canonical_url)
        page_content = await self.__download(canonical_url, self.__max_document_bytes)
        page = self.__page_parser.parse(_decode_page(page_content), canonical_url)
        document_content = await self.__download(page.document_url, self.__max_document_bytes)
        text = self.__docx_parser.parse(document_content)
        logger.info("duma bill fetch completed: url=%s stage=%s", canonical_url, page.stage_code)
        return BillSnapshot(
            page.url,
            page.bill_number,
            page.title,
            page.stage,
            page.stage_code,
            text,
            page.document_url,
            page.updated_at,
            page.published_at,
        )

    async def close(self) -> None:
        await self.__client.aclose()

    async def __download(self, url: str, max_bytes: int) -> bytes:
        try:
            async with self.__client.stream("GET", url) as response:
                response.raise_for_status()
                _validate_final_url(str(response.url), url)
                return await _read_limited(response, max_bytes)
        except (httpx.HTTPError, ValueError) as error:
            raise NpaSourceUnavailableError(f"State Duma fetch failed: url={url}") from error
