"""One scored impact dimension of a ranked event, with the model's grounding."""

from typing import Literal

from pydantic import BaseModel

ImpactDimension = Literal["finance", "reputation", "technology", "competition"]
IMPACT_DIMENSIONS: tuple[ImpactDimension, ...] = (
    "finance",
    "reputation",
    "technology",
    "competition",
)


class ImpactReasonOut(BaseModel):
    dimension: ImpactDimension
    # 0 (no evidenced consequence) … 3 (direct, urgent or broadly disruptive).
    score: int
    reason: str
