"""`RuleScorer` — sum the weights of every rule that applies, clamp to 0..1."""

from collections.abc import Sequence

from .model import Score, ScoreRule

MIN_SCORE = 0.0
MAX_SCORE = 1.0


class RuleScorer[EntityT]:
    """Thresholds are not here: how strict to be is the caller's decision, what counts
    is the domain's."""

    def __init__(self, rules: Sequence[ScoreRule[EntityT]]) -> None:
        self.__rules = tuple(rules)

    def score(self, entity: EntityT) -> Score:
        fired = tuple(rule for rule in self.__rules if rule.applies(entity))
        total = sum(rule.weight for rule in fired)
        return Score(
            value=min(MAX_SCORE, max(MIN_SCORE, total)),
            fired=tuple(rule.name for rule in fired),
        )
