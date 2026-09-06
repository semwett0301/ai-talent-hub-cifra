"""One semantic reason a news event can matter to the monitored company."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Facet:
    name: str
    description: str
    bm25_terms: tuple[str, ...] = ()
    reranker_guidance: str = ""

    @property
    def semantic_query(self) -> str:
        return f"{self.name}. {self.description}".strip()
