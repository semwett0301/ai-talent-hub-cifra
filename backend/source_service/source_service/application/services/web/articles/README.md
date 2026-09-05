# services/web/articles

From a candidate link to an accepted article. The three services here are siblings, each
called by `WebCrawl` in turn — none drives another. Each takes the whole list, touches only
the status that is its own and passes everything else through untouched, so the
orchestrator never sorts articles by status.

- `harvest.py` — `ArticleHarvest.run(candidates, stats) -> list[Article]`
  (`DATED` | `FETCHED` | `REJECTED`): downloads the candidate pages batch by batch
  (`article_batch_size`) and decides how far down the list it is still worth paying to go —
  it holds no verdict of its own. Calls `choose_container` once per site and stops after
  `out_of_scope_consecutive_batches` batches whose printed dates all fell before the
  window. Candidates are ordered by relevance, not by time, so a single old page never ends
  a run.
- `fetching.py` — `ArticleFetching`: `choose_container(sample_url)` once per site picks the
  text container; `run(batch, selector)` takes `DISCOVERED` and returns `DATED` (a
  machine-readable date was in the markup), `FETCHED` (text but no date) or
  `REJECTED(FETCH_FAILED | TOO_SHORT)`. Builds `ArticleContent`; raw HTML stops here.
- `date_resolution.py` — `DateResolution`: `FETCHED → DATED | REJECTED(NO_DATE |
  NOT_ARTICLE)`. Only pages without a machine-readable date are asked; the `CrawlLlm` port
  reads `content.text`, a guess is accepted at `llm_date_min_confidence` and stamped
  `DateSource.LLM`. Without a resolver (or with `llm_date_fallback=false`) they are all
  `NO_DATE`. Called once per site, so it opens its own `LlmCallBudget` — at most one call
  per candidate (`max_article_candidates_per_site`), `llm_date_concurrency` at once.
- `judgement.py` — `ArticleJudgement`: `DATED → ACCEPTED | REJECTED(OUT_OF_WINDOW |
  NO_TITLE)` via `FreshnessWindow` and the title fallback. No I/O.
- `state/` — per-run state (`StaleStreak`), built in `run()` and never injected.

Notes: the early stop reads **markup** dates only — the LLM fallback runs after the whole
download, so waiting for it inside the loop would defeat the point of stopping. Thresholds
come from `WebCrawlSettings`; the rules (`FreshnessWindow`, `accept()`) are the domain's.
`merge_duplicates` is deliberately **not** here: an article's identity is only known after
the fetch, and collapsing duplicates is the orchestrator's last step over the whole site.
