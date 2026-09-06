# ranking

- `company_profile.json` — packaged GS Labs relevance facets adapted from the supplied pipeline.
- `company_profile_loader.py` — validated packaged profile loading.
- `openrouter_ranking_models.py` — structured impact judge plus `/rerank` adapter.
- `prompts.py` — stable cluster-impact policy.

The ranking service reuses the local BGE vectors already persisted by dedup; no second embedding
provider or duplicate vector store is introduced.
