# articles/state

State that belongs to **one site crawl**, not to the service. `ArticleHarvest` builds these
inside `run()`; injecting them would leak one site's progress into another site's crawl.

- `stale_streak.py` — `StaleStreak`: how many batches in a row came back with nothing
  fresh. `should_stop(fetched)` records a batch and answers whether the run has left the
  freshness window for good. A batch counts only when at least
  `out_of_scope_min_resolved_dates_per_batch` dates were readable in the markup — a batch
  of failed fetches says nothing about the age of the archive.

Notes: reads only markup dates (`DATED` after `ArticleFetching`); the LLM date fallback
runs later and is deliberately not waited for here.
