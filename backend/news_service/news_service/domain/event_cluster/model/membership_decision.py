"""One verifier verdict for one candidate news item."""

from dataclasses import dataclass
from typing import Literal

type Decision = Literal["SAME", "DIFFERENT", "UNCERTAIN"]


@dataclass(frozen=True, slots=True)
class MembershipDecision:
    decision: Decision
    hard_conflicts: tuple[str, ...] = ()
    critical_unknowns: tuple[str, ...] = ()
