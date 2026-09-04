from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dateutil import parser as dtparser  # type: ignore[import-untyped]

_RU_MONTHS = {
    "января": "January",
    "февраля": "February",
    "марта": "March",
    "апреля": "April",
    "мая": "May",
    "июня": "June",
    "июля": "July",
    "августа": "August",
    "сентября": "September",
    "октября": "October",
    "ноября": "November",
    "декабря": "December",
    "январь": "January",
    "февраль": "February",
    "март": "March",
    "апрель": "April",
    "май": "May",
    "июнь": "June",
    "июль": "July",
    "август": "August",
    "сентябрь": "September",
    "октябрь": "October",
    "ноябрь": "November",
    "декабрь": "December",
}


def _normalize_ru_months(value: str) -> str:
    out = value
    for ru, en in _RU_MONTHS.items():
        out = re.sub(rf"\b{ru}\b", en, out, flags=re.I)
    return out


def parse_date(value: str | None, timezone: str) -> datetime | None:
    if value is None or not str(value).strip():
        return None
    raw = _normalize_ru_months(str(value).strip())
    tz = ZoneInfo(timezone)
    dayfirst = bool(re.search(r"\b\d{1,2}[./]\d{1,2}[./]\d{4}\b", raw))
    try:
        parsed = dtparser.parse(raw, dayfirst=dayfirst, fuzzy=True, tzinfos={"MSK": tz, "МСК": tz})
    except (ValueError, TypeError, OverflowError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz)


def is_recent(value: datetime, days: int, timezone: str, now: datetime | None = None) -> bool:
    tz = ZoneInfo(timezone)
    current = (now or datetime.now(tz)).astimezone(tz)
    return current - timedelta(days=days) <= value.astimezone(tz) <= current + timedelta(hours=12)


def is_older_than_window(
    value: datetime, days: int, timezone: str, now: datetime | None = None
) -> bool:
    """Return true only for dates before the recent-news window, not future dates."""
    tz = ZoneInfo(timezone)
    current = (now or datetime.now(tz)).astimezone(tz)
    return value.astimezone(tz) < current - timedelta(days=days)
