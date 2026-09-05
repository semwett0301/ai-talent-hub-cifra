# services/article

What happens to an article once its page is fetched. Each service takes articles of one
status and returns them one stage further or rejected with a reason.

- `date_resolution.py` — `DateResolution`: `FETCHED → DATED | REJECTED(NO_DATE |
  NOT_ARTICLE)`. Only pages without a machine-readable date get here; asks the
  `CrawlLlm` port over `content.text`, accepts at
  `llm_date_min_confidence`, stamps `DateSource.LLM`. Without a resolver (or with
  `llm_date_fallback=false`) everything is `NO_DATE`. `budget()` hands out one
  `LlmDateBudget` per crawl.
- `llm_date_budget.py` — `LlmDateBudget`: hard cap on LLM calls per site
  (`llm_date_max_calls_per_site`) plus a concurrency gate; past the cap `run` returns
  `(None, False)` without calling.
- `article_judgement.py` — `ArticleJudgement`: `DATED → ACCEPTED | REJECTED(OUT_OF_WINDOW |
  NO_TITLE)` via `FreshnessWindow` and the title fallback. No I/O.

Notes: both services raise on an article of the wrong status — the orchestrator routes by
status, a mismatch is a bug, not data. Thresholds come from `WebCrawlSettings`; the rules
(`FreshnessWindow`, `accept()`) are the domain's.
