"""Company context the impact judge grounds its scores in."""

from dataclasses import dataclass

from news_service.domain.company_profile.model.facet import Facet


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    name: str
    description: str
    facets: tuple[Facet, ...]
    language: str = "ru"

    @property
    def judge_context(self) -> str:
        lines = [f"Company: {self.name}", self.description, "Relevance facets:"]
        for facet in self.facets:
            lines.append(f"- {facet.name}: {facet.description}")
            if facet.judging_guidance:
                lines.append(f"  Guidance: {facet.judging_guidance}")
        return "\n".join(lines)
