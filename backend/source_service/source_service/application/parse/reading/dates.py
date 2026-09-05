"""Free-form date parsing — the *how* of turning a printed date into a `datetime`."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from dateutil import parser as dtparser  # type: ignore[import-untyped]

MOSCOW_ABBREVIATIONS = ("MSK", "МСК")
DAY_FIRST_RE = re.compile(r"\b\d{1,2}[./]\d{1,2}[./]\d{4}\b")

_RU_MONTHS = {
    "январ": "January",
    "феврал": "February",
    "март": "March",
    "апрел": "April",
    "ма[йя]": "May",
    "июн": "June",
    "июл": "July",
    "август": "August",
    "сентябр": "September",
    "октябр": "October",
    "ноябр": "November",
    "декабр": "December",
}
# Stem + case ending: "марта", "март", "сентября", "сентябрь", "мая", "май".
_RU_MONTH_RE = re.compile(r"\b(" + "|".join(_RU_MONTHS) + r")[аья]?\b", re.IGNORECASE)

# Genitive form, as printed in running text: "13 марта", "5 сентября". The single source
# for every "does this text look like a date" regex elsewhere in `parse/`.
RU_MONTH_NAMES = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def parse_date(value: str | None, timezone: str) -> datetime | None:
    """Lenient parse of a date string in Russian or English; `None` when unparseable.
    A naive result gets the site's timezone."""
    if value is None or not str(value).strip():
        return None

    zone = ZoneInfo(timezone)
    text = _RU_MONTH_RE.sub(_english_month, str(value).strip())
    try:
        parsed = dtparser.parse(
            text,
            dayfirst=bool(DAY_FIRST_RE.search(text)),
            fuzzy=True,
            tzinfos=dict.fromkeys(MOSCOW_ABBREVIATIONS, zone),
        )
    except (ValueError, TypeError, OverflowError):
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(zone)


def _english_month(match: re.Match[str]) -> str:
    stem = match.group(1).lower()
    return next(english for ru, english in _RU_MONTHS.items() if re.fullmatch(ru, stem))
