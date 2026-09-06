"""Embedding contract for retrieval summaries."""

from typing import Protocol


class SummaryEmbedder(Protocol):
    def embed(self, summaries: list[str]) -> list[list[float]]: ...
