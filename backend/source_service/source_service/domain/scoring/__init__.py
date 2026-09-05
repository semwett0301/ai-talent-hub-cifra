"""Scoring — the generic mechanism: weighted rules summed into a clamped score.

Entity-specific rule sets live with their entities (`article/rules`, `hub/rules`); only
what both share is here: the `ScoreRule` / `Score` values, `RuleScorer`, and the URL
vocabulary neither entity owns (`terms.py`).
"""

from .model import Score, ScoreRule
from .scorer import RuleScorer

__all__ = ["RuleScorer", "Score", "ScoreRule"]
