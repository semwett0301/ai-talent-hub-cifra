"""`ScoreRule` — one named, weighted observation about an entity."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreRule[EntityT]:
    """`applies(entity)` says whether the observation holds; `weight` is what it adds
    (negative for a penalty). Rules are values, not collaborators: a plain predicate
    keeps each one a one-liner that is testable on its own."""

    name: str
    weight: float
    applies: Callable[[EntityT], bool]
