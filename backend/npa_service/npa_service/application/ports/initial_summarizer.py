"""Port for explaining the first available version of a bill."""

from typing import Protocol

from npa_service.domain import BillSnapshot


class InitialSummarizer(Protocol):
    """Builds a detailed, plain-language overview without comparing revisions."""

    async def summarize(self, snapshot: BillSnapshot) -> str: ...
