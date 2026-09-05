# domain/scoring/model

- `rule.py` — `ScoreRule[T]`: one named, weighted observation about an entity; a value
  with a plain predicate, not a collaborator, so each rule is a one-liner testable alone.
- `score.py` — `Score`: the result — value clamped to 0..1 and the names of the rules
  that fired, for logs and tests.
