# domain/event_cluster

The `EventCluster` aggregate: the group of `EventSummary` items believed to describe the same
real-world event. Deduplication (deciding membership) and ranking (scoring relevance) are two
processes that both act on this one entity — neither is itself a domain concept, which is why
they no longer name a package.

- `event_cluster.py` — `EventCluster`: the entity. Bounded oldest/newest-anchor view a
  repository loads for one cluster (summaries, `published_at`, `source_score`, `member_count`).
- `model/` — what an `EventCluster` is made of, and what forms during its formation:
  `CandidateCluster`, `Precluster`, `ClusterAssignment`, `MembershipDecision`,
  `ImpactAssessment`, `RankingResult`, `RelevanceCategory`. See `model/README.md`.
- `rules/` — what judges an `EventCluster`: fail-closed membership combination (`membership.py`),
  BM25 lexical relevance (`bm25.py`), the relevance product formula (`scoring.py`). See
  `rules/README.md`.
