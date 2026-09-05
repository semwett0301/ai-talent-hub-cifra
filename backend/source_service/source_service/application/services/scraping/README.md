# services/scraping

How to reach a site's publications. One class per module, dependencies in the constructor
(ports + `WebCrawlSettings`), one `run`. Between services articles travel as `Article` and
the contract is the **status**; `FetchedPage` (the port's return type) never leaves the
service that fetched it.

- `web_crawl.py` — `WebCrawl.run(site) -> list[Article]`: the orchestrator. Order, routing
  by status (markup-dated → judgement, undated → `DateResolution` first, rejected carried
  for the report), the early stop after consecutive only-old batches, the domain's
  `merge_duplicates` on the result, one `web crawl finished` line from `CrawlRun`. Takes its six stages as one `CrawlStages` (defined alongside,
  wired once in `deps.py`).
- `hub_discovery.py` — `HubDiscovery.run(site) -> list[Hub]`: home page → same-site,
  non-article links one and two clicks deep → `CrawlLlm.classify_listing` per page (bounded by
  `listing_llm_max_calls_per_site`) → hubs above `listing_llm_min_confidence`, ordered by
  `HUB_SCORER`. Home page as the only hub when nothing is confirmed or no classifier.
- `card_collection.py` — `CardCollection.run(hubs) -> list[Article]` (`DISCOVERED`): each
  hub page after page, cards in order; the first card dated before the window ends the
  hub; next page = `hub.next_page` for the first hop, then `next_listing_page`.
- `fallback_discovery.py` — `FallbackDiscovery.run(site) -> list[Article]`: only when the
  listings yielded nothing. `PageCrawler.adaptive_discover` → hub-like pages by
  `HUB_SCORER` → `best_first_discover` per hub, consumed page by page; every N pages after
  the first M (`date_probe_start_page` / `date_probe_interval_pages`), the page's
  publication date is read — older than the window ends that hub's crawl. The adapter only
  streams pages; stopping is this strategy's decision.
- `article_fetching.py` — `ArticleFetching`: `choose_container(sample_url)` once per site
  picks the text container; `run(batch, selector)` takes `DISCOVERED` and returns `DATED`
  (a machine-readable date was in the markup), `FETCHED` (text but no date) or
  `REJECTED(FETCH_FAILED | TOO_SHORT)`. Builds `ArticleContent`; raw HTML stops here.

Notes: batching (`article_batch_size`) and the early stop are the orchestrator's — they are
decisions about the process, not about an article. What is left here is crawl strategy:
which pages to fetch, in what order, how deep, when to stop. Ranking, selection, dedupe
and every judgement about an article or a hub are domain rules (`is_article_like`,
`select_candidates`, `select_hubs`, `merge_hubs`, `merge_duplicates`, `FreshnessWindow`);
the services only pass the thresholds from settings.
