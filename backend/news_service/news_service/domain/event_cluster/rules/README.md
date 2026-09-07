# domain/event_cluster/rules

- `membership.py` — `normalize_decision` (fail-closed: a verifier verdict counts as `SAME`
  only with no hard conflict and no critical unknown), `combine_decisions` (several
  candidate-cluster verdicts collapse to one).
- `bm25.py` — dependency-free lexical relevance against company facets.
- `scoring.py` — the deterministic impact/urgency/source/BM25 product formula and its
  relevance categories.

All calculations are deterministic and independent of persistence or model providers.
