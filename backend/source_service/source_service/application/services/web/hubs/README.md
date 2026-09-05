# services/web/hubs

Which pages of a site list its publications. Nothing here reads a listing's cards or
opens an article — the answer is a ranked `list[Hub]` and nothing else.

- `discovery.py` — `HubDiscovery.run(site) -> list[Hub]`: home page → same-site,
  non-article links, up to `listing_discovery_max_depth` clicks deep → classify (via
  `ListingClassifier`) → hubs above `listing_llm_min_confidence`, ordered by `HUB_SCORER`.
  Home page as the only hub when nothing is confirmed or there is no classifier. Opens a
  fresh `Frontier` and a fresh `ListingClassifier.budget()` at the top of `run()` and
  threads both down as plain parameters — never stores them on `self`: one `HubDiscovery`
  instance serves every site the scheduler crawls, often several at once.
- `listing_classifier.py` — `ListingClassifier(llm, settings)`: a per-process singleton
  with no state of its own. `budget()` opens a per-site `LlmCallBudget`
  (`listing_max_pages_per_site` calls in total, `listing_llm_concurrency` at once) that the
  caller passes to every `classify(pages, budget)` of that site; `classify` asks
  `CrawlLlm.classify_listing` per page concurrently and logs the outcome itself — a page
  the budget can't afford is dropped before its snapshot is even built. The snapshot never
  leaves this module: `ClassifiedPage` carries the already-resolved `next_page`.
- `state/` — per-run state (`Frontier`), built in `run()` and never injected.

Notes: everything scoped to one site (the frontier, the LLM budget) is created in
`HubDiscovery.run` and passed down, never held on a service — the services themselves are
shared by every concurrent crawl. One discovered page costs at most one `classify_listing`
call, so `listing_max_pages_per_site` is the single cap for both the fetches and the LLM
calls. `state/` is package-internal: nothing there is re-exported from `__init__.py` and no
other stage may reach for it.
