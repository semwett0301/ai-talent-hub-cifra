"""Explainable company impact and urgency for one event cluster."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ImpactAssessment:
    finance_score: int
    finance_reason: str
    reputation_score: int
    reputation_reason: str
    technology_score: int
    technology_reason: str
    competition_score: int
    competition_reason: str
    urgency_basis: str
    urgency_reason: str
    urgency_score: int
    raw: dict[str, Any]

    @property
    def impact_score(self) -> int:
        return max(
            self.finance_score,
            self.reputation_score,
            self.technology_score,
            self.competition_score,
        )
