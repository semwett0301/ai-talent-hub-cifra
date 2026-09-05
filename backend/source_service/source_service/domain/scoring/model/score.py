"""`Score` — the result of scoring: the value and the rules that produced it."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    value: float  # clamped to 0..1
    fired: tuple[str, ...]  # names of the rules that applied, for logs and tests
