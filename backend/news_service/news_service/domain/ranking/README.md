# ranking

Pure value objects for scoring one deduplicated event cluster as one unit.

- `company_profile.py`, `facet.py` — monitored-company relevance context.
- `cluster_ranking_target.py` — bounded oldest/newest cluster anchors from persistence.
- `impact_assessment.py` — explainable LLM impact and urgency assessment.
- `relevance_category.py`, `ranking_result.py` — stable persisted result vocabulary.
- `rules/` — BM25, dense similarity, reciprocal-rank fusion, and the product formula.
