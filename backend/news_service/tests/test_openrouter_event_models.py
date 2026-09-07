import uuid
from datetime import UTC, datetime

import pytest
from common.entities.news import NewsDTO, SourceType
from common.entities.source import SourceReliability
from news_service.application.errors import EventModelError
from news_service.domain.event_summary import NewsTarget
from news_service.infrastructure.dedup.openrouter_event_models import (
    _build_summary,
    _EventExtraction,
)

# The positive alert sample: vedomosti.ru, 2026-09-04,
# "Для подключаемых к госсистемам сервисов усилят защиту" — 568-ФЗ, ПП № 1024, приказ ФСБ № 321.
VEDOMOSTI = NewsTarget(
    uuid.UUID("11111111-1111-1111-1111-111111111111"),
    NewsDTO(
        source_id=uuid.uuid4(),
        source_link="https://www.vedomosti.ru",
        source_name="Ведомости",
        source_type=SourceType.WEB,
        source_reliability=SourceReliability.HIGH,
        url="https://www.vedomosti.ru/technology/articles/2026/09/04/1226133-dlya-podklyuchaemih-k-gossistemam-servisov-usilyat-zaschitu",
        title="Для подключаемых к госсистемам сервисов усилят защиту",
        text=(
            "ФСБ распространила требования к криптографической защите на внешние облачные "
            "сервисы, обеспечивающие работу ГИС. Основание — закон № 568-ФЗ, постановление "
            "Правительства № 1024 и приказ ФСБ № 321."
        ),
        published_at=datetime(2026, 9, 4, tzinfo=UTC),
    ),
)


def _extraction(*flags: bool) -> _EventExtraction:
    regulation, concerns, useful = flags
    return _EventExtraction(
        primary_event_found=True,
        summary="ФСБ распространила требования к криптозащите на облачные сервисы для ГИС.",
        is_russian_regulation=regulation,
        concerns_company=concerns,
        regulation_is_useful=useful,
    )


def test_all_three_flags_raise_the_alert():
    summary = _build_summary(VEDOMOSTI, _extraction(True, True, True))

    assert summary.is_regulatory_alert
    assert summary.has_primary_event
    assert summary.news_id == VEDOMOSTI.news_id


@pytest.mark.parametrize("flags", [(True, True, False), (True, False, True), (False, True, True)])
def test_any_missing_flag_keeps_the_item_unflagged(flags: tuple[bool, bool, bool]):
    assert not _build_summary(VEDOMOSTI, _extraction(*flags)).is_regulatory_alert


def test_missing_or_empty_summary_is_an_error():
    with pytest.raises(EventModelError):
        _build_summary(VEDOMOSTI, None)
