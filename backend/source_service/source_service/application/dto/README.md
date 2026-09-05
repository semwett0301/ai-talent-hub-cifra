# dto

Application request/response schemas (Pydantic), grouped by resource. Distinct from
`common.entities.news`, which is the **bus** contract (`NewsDTO`).

- `source/` — DTOs for the `Source` resource.
- `crawl_run.py` — `CrawlRun`: what one WEB crawl did (hubs, candidates, fetched, verdicts
  by status and reason, LLM-dated count, early stop) for the single summary log line.

Notes: use cases take/return these; the API layer passes them through. Output DTOs
set `from_attributes=True` to build from the ORM `Source`.
