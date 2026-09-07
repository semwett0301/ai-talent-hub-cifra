"""One ordered stage in the post-summary news pipeline."""

from typing import Protocol


class NewsPipelineStage(Protocol):
    async def process(self, urls: list[str]) -> None: ...
