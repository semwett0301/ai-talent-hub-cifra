"""`FreshnessWindow` — which publication dates count as news right now."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

# A date a few hours "in the future" is a timezone artefact, not a fake.
FUTURE_TOLERANCE = timedelta(hours=12)


class FreshnessWindow(BaseModel, frozen=True):
    """The last `days` days in the site's timezone, plus a small future tolerance."""

    days: int = Field(ge=1)
    timezone: str

    def contains(self, value: datetime, now: datetime | None = None) -> bool:
        """Fresh: not older than `days`, not far in the future."""
        current = self.__now(now)
        moment = value.astimezone(current.tzinfo)
        return current - timedelta(days=self.days) <= moment <= current + FUTURE_TOLERANCE

    def is_before(self, value: datetime, now: datetime | None = None) -> bool:
        """Strictly older than the window — a future date is *not* old."""
        current = self.__now(now)
        return value.astimezone(current.tzinfo) < current - timedelta(days=self.days)

    def __now(self, now: datetime | None) -> datetime:
        zone = ZoneInfo(self.timezone)
        return (now or datetime.now(zone)).astimezone(zone)
