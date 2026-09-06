"""Company context shared by semantic retrieval and impact assessment."""

from dataclasses import dataclass

from news_service.domain.ranking.facet import Facet


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    name: str
    description: str
    facets: tuple[Facet, ...]
    language: str = "ru"

    @property
    def reranker_query(self) -> str:
        lines = [f"Company: {self.name}", self.description, "Relevance facets:"]
        for facet in self.facets:
            lines.append(f"- {facet.name}: {facet.description}")
            if facet.reranker_guidance:
                lines.append(f"  Guidance: {facet.reranker_guidance}")
        return "\n".join(lines)
