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
        "О внесении изменений в порядок рассмотрения обращений граждан",
        "Рассмотрение законопроекта в первом чтении",
        "arrh_d4",
        """Статья 1. Государственные органы, органы местного самоуправления и подведомственные
организации рассматривают письменные обращения граждан в срок не более 30 календарных дней.

Статья 2. Ответ направляется заявителю в электронной форме, если обращение подано через
единый портал государственных услуг. По вопросам, требующим запроса документов у другого
органа, срок может быть продлён не более чем на 15 календарных дней с уведомлением заявителя.

Статья 3. Руководитель органа обеспечивает учёт обращений и ежеквартально публикует сведения
о количестве рассмотренных обращений и среднем сроке подготовки ответов.""",
        f"{SIMULATION_DOCUMENT_URL}/v1",
        _OBSERVED_AT,
        None,
    ),
    BillSnapshot(
        SIMULATION_URL,
        "9999999-9",
        "О внесении изменений в порядок рассмотрения обращений граждан",
        "Рассмотрение законопроекта во втором чтении",
        "arrh_d5",
        """Статья 1. Государственные органы, органы местного самоуправления и подведомственные
организации рассматривают обращения граждан в срок не более 20 календарных дней.

Статья 2. Ответ направляется заявителю в электронной форме, если обращение подано через
единый портал государственных услуг. По вопросам, требующим межведомственного запроса,
срок может быть продлён не более чем на 10 календарных дней с обязательным уведомлением.

Статья 3. Руководитель органа обеспечивает учёт обращений, ежеквартально публикует сведения
о сроках ответов и назначает ответственное должностное лицо за контроль просроченных обращений.

Статья 4. Изменения применяются к обращениям, поступившим после 1 января 2027 года.""",
        f"{SIMULATION_DOCUMENT_URL}/v2",
        _OBSERVED_AT,
        None,
    ),
    BillSnapshot(
        SIMULATION_URL,
        "9999999-9",
        "О внесении изменений в порядок рассмотрения обращений граждан",
        "Опубликование закона",
        "arrh_d11",
        """Статья 1. Государственные органы, органы местного самоуправления и подведомственные
организации рассматривают обращения граждан в срок не более 20 календарных дней.

Статья 2. Электронный ответ направляется через единый портал государственных услуг. При
межведомственном запросе срок продлевается не более чем на 10 календарных дней с уведомлением.

Статья 3. Руководитель органа назначает ответственного за контроль сроков, а сведения о числе
и сроках рассмотренных обращений публикуются ежеквартально.

Статья 4. Закон вступает в силу с 1 января 2027 года.""",
        f"{SIMULATION_DOCUMENT_URL}/v3",
        _OBSERVED_AT,
        _OBSERVED_AT,
    ),
)
