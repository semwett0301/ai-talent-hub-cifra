# domain/scoring

The generic scoring mechanism, shared by every entity that is scored. Nothing here knows
`Article` or `Hub`; their rule sets live in `article/rules` and `hub/rules`.

- `model/` — the values: `ScoreRule[T]` (name, weight, predicate over the entity) and
  `Score` (clamped value + names of the rules that fired). See `model/README.md`.
- `scorer.py` — `RuleScorer[T]`: sums the weights of the rules that apply, clamps to 0..1.
- `terms.py` — the URL vocabulary that belongs to *neither* entity: section/junk
  segments and the article-shaped URL regexes both rule sets read (as a bonus for an
  article, as a penalty for a hub). Anything specific to one entity lives with it.

Notes: `RuleScorer[T]` is generic over the entity, so a new entity gets scoring by
listing its rules — no new mechanism. Log `Score.fired` when a decision looks wrong.
