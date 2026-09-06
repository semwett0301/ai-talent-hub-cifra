"""A three-step NPA source for local UI demonstrations."""

import re
from dataclasses import replace
from datetime import UTC, datetime

from common.core.logging import get_logger

from npa_service.application.errors import InvalidNpaUrlError
from npa_service.application.ports import NpaSource
from npa_service.domain import BillSnapshot

SIMULATION_URL = "https://sozd.duma.gov.ru/bill/9999999-9"
SIMULATION_DOCUMENT_URL = "https://sozd.duma.gov.ru/download/npa-simulation"
SIMULATION_URL_PATTERN = re.compile(r"https://sozd\.duma\.gov\.ru/bill/9999999-\d+")
logger = get_logger(__name__)


class SimulationSource(NpaSource):
    def __init__(self) -> None:
        self.__fetch_counts: dict[str, int] = {}

    async def fetch(self, url: str) -> BillSnapshot:
        if not SIMULATION_URL_PATTERN.fullmatch(url):
            raise InvalidNpaUrlError(f"simulation accepts URLs like: {SIMULATION_URL}")
        fetch_count = self.__fetch_counts.get(url, 0)
        index = min(fetch_count, len(_SNAPSHOTS) - 1)
        self.__fetch_counts[url] = fetch_count + 1
        snapshot = replace(_SNAPSHOTS[index], url=url, bill_number=url.rsplit("/", 1)[-1])
        logger.info("npa simulation fetched: url=%s step=%d", url, index + 1)
        return snapshot


_OBSERVED_AT = datetime(2026, 9, 6, tzinfo=UTC)
_SNAPSHOTS = (
    BillSnapshot(
        SIMULATION_URL,
        "9999999-9",
        "Тестовый законопроект о сроках ответа на обращения",
        "Рассмотрение законопроекта в первом чтении",
        "arrh_d4",
        "Статья 1. Орган обязан ответить на обращение в течение 30 дней.",
        f"{SIMULATION_DOCUMENT_URL}/v1",
        _OBSERVED_AT,
        None,
    ),
    BillSnapshot(
        SIMULATION_URL,
        "9999999-9",
        "Тестовый законопроект о сроках ответа на обращения",
        "Рассмотрение законопроекта во втором чтении",
        "arrh_d5",
        "Статья 1. Орган обязан ответить на обращение в течение 15 дней.",
        f"{SIMULATION_DOCUMENT_URL}/v2",
        _OBSERVED_AT,
        None,
    ),
    BillSnapshot(
        SIMULATION_URL,
        "9999999-9",
        "Тестовый закон о сроках ответа на обращения",
        "Опубликование закона",
        "arrh_d11",
        "Статья 1. Орган обязан ответить на обращение в течение 10 дней.",
        f"{SIMULATION_DOCUMENT_URL}/v3",
        _OBSERVED_AT,
        _OBSERVED_AT,
    ),
)
