# services/scraping

How to reach a site's publications. One class per module, dependencies in the constructor
(ports + `WebCrawlSettings`), one `run`. Between services articles travel as `Article` and
the contract is the **status**; `FetchedPage` (the port's return type) never leaves the
service that fetched it.

- `web_crawl.py` — `WebCrawl.run(source) -> list[Article]`: the orchestrator. Builds the
  `Site` from the `Source` row, routes by status (markup-dated → judgement, undated →
  `DateResolution` first, rejected carried for the report), the early stop after
  consecutive only-old batches, the domain's `merge_duplicates` on the result, one
  `web crawl finished` line from `CrawlRun`. Takes its five stages as one `CrawlStages`
  plus the `SourceRepository` port (wired once in `deps.py`): when the listing search finds
  no candidate at all, it marks the source `is_relevant=false` itself — no fallback.
- `hub_discovery.py` — `HubDiscovery.run(site) -> list[Hub]`: home page → same-site,
  non-article links, up to `listing_discovery_max_depth` clicks deep → `CrawlLlm.classify_listing`
  per page (bounded by `listing_llm_max_calls_per_site`) → hubs above
  `listing_llm_min_confidence`, ordered by `HUB_SCORER`. Home page as the only hub when
  nothing is confirmed or no classifier.
- `card_collection.py` — `CardCollection.run(hubs) -> list[Article]` (`DISCOVERED`): each
  hub page after page, cards in order; the first card dated before the window ends the
  hub; next page = `hub.next_page` for the first hop, then `next_listing_page`.
- `article_fetching.py` — `ArticleFetching`: `choose_container(sample_url)` once per site
  picks the text container; `run(batch, selector)` takes `DISCOVERED` and returns `DATED`
  (a machine-readable date was in the markup), `FETCHED` (text but no date) or
  `REJECTED(FETCH_FAILED | TOO_SHORT)`. Builds `ArticleContent`; raw HTML stops here.

Notes: batching (`article_batch_size`) and the early stop are the orchestrator's — they are
decisions about the process, not about an article. What is left here is crawl strategy:
which pages to fetch, in what order, how deep, when to stop. Ranking and every judgement
about an article or a hub are domain rules (`is_article_like`, `hub_score`, `rank_hubs`,
`merge_duplicates`, `FreshnessWindow`); the services only pass the thresholds from settings.
There is no fallback discovery: if the listing route finds nothing, `WebCrawl` marks the
source `is_relevant=false` itself instead of guessing further.
