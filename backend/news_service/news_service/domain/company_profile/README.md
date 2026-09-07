# domain/company_profile

The `CompanyProfile` aggregate: the monitored company the impact judge grounds its scores in.
Reference data, not derived from any news item — loaded once from a packaged profile.

- `company_profile.py` — `CompanyProfile`: name, description, facets, `judge_context` (the
  prompt text built from them).
- `model/` — `Facet`: one semantic reason a news event can matter to the company. See
  `model/README.md`.
