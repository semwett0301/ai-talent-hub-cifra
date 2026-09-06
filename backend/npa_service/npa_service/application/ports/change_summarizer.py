"""Port for explaining the difference between two bill texts."""

from typing import Protocol

from npa_service.domain import ChangeSummary


class ChangeSummarizer(Protocol):
    async def summarize(self, previous_text: str, current_text: str) -> ChangeSummary: ...
