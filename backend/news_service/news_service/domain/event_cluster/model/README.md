# domain/event_cluster/model

- `candidate_cluster.py` — `CandidateCluster`: a pgvector-retrieved cluster and its identity
  anchors, found while looking for a match for one pending `EventSummary`.
- `candidate_query.py` — `CandidateQuery`: bounded pgvector lookup parameters for one pending
  event summary.
- `precluster.py` — `Precluster`: one trusted cluster anchor set with summaries to screen for
  membership, batched for one verifier call.
- `membership_decision.py` — `MembershipDecision` / `Decision`: one verifier verdict for one
  candidate news item.
- `cluster_assignment.py` — `ClusterAssignment`: the durable event-cluster assignment for one
  news row.
- `impact_assessment.py` — `ImpactAssessment`: explainable company impact and urgency for one
  event cluster.
- `ranking_result.py` — `RankingResult`: persistable ranking result calculated once for a
  deduplicated cluster.
- `relevance_category.py` — `RelevanceCategory`: stable output categories for corporate news
  relevance.
