from datetime import datetime
from zoneinfo import ZoneInfo

from source_service.application.parse import parse_date
from source_service.domain import FreshnessWindow


def test_parse_russian_date_and_window():
    value = parse_date("3 сентября 2026, 12:30 МСК", "Europe/Moscow")
    assert value is not None
    now = datetime(2026, 9, 4, 0, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    window = FreshnessWindow(days=3, timezone="Europe/Moscow")
    assert window.contains(value, now=now)
    assert not window.is_before(value, now=now)

    old = parse_date("30 августа 2026", "Europe/Moscow")
    assert old is not None
    assert window.is_before(old, now=now)
    assert not window.contains(old, now=now)


def test_unparseable_and_blank_dates_are_none():
    assert parse_date("", "Europe/Moscow") is None
    assert parse_date("not a date at all", "Europe/Moscow") is None
