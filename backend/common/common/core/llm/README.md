# common.core.llm

Infrastructure every service reuses when it talks to a model. The **model client itself
is not here** — a service brings its own adapter (`CrawlLlm` in `source_service`); what
lives here is the traffic control every such adapter needs.

- `call_budget.py` — `LlmCallBudget`: one budget per run (a site crawl, a batch, a job).
  Caps the **total** number of LLM calls (`max_calls`, `0` = unlimited) and how many run
  **at once** (`concurrency`). `await budget.run(action)` returns the action's answer, or
  `None` when the budget is spent — the action is then never awaited, so anything
  expensive (snapshot building, prompt assembly) belongs inside it. `budget.used` is the
  number of calls actually made, for the log line at the end of the run.

Notes: the budget is a plain object, not a singleton — create one per run and pass it to
every stage that shares the cap (`DateResolution.budget()` and `ListingClassifier.budget()`
do exactly this). It is safe under `asyncio.gather`: the reservation is taken under a lock, so concurrent callers never
overshoot `max_calls`. Limits are **not** read from settings here — the caller passes its
own numbers (`WEB_CRAWL_LISTING_LLM_*`, `WEB_CRAWL_LLM_DATE_*`), so one service can run
several budgets with different caps.
