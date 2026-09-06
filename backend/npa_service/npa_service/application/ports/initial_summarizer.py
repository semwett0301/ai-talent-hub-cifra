"""Port for explaining the first available version of a bill."""

from typing import Protocol

from npa_service.domain import BillSnapshot, InitialSummary


class InitialSummarizer(Protocol):
    """Builds a short plain-language overview and a readable bill title."""

    async def summarize(self, snapshot: BillSnapshot) -> InitialSummary: ...
