# crawlers

The adapters that talk to the web and to the LLM — the only place in the service that
imports `crawl4ai`, `feedparser` and `litellm`.

- `crawl4ai_fetcher.py` — `Crawl4AiPageFetcher` → `PageFetcher`: wraps `AsyncWebCrawler`
  with `AsyncHTTPCrawlerStrategy` (lightweight HTTP fetch, no browser) to fetch a URL's
  raw body — feed XML, or an article's HTML. Owns a `start`/`close` lifecycle driven from
  `main.py`'s lifespan.
- `feedparser_reader.py` — `FeedparserFeedReader(page_fetcher)` → `FeedReader`: fetches
  the feed body through `PageFetcher`, parses it with feedparser and maps each item to a
  `FeedEntry`: `title`/`summary` with markup stripped, `published_at` (`published`, else
  `updated`), `updated_at` (`updated` only when it differs from `published`), `tags` (category
  terms, deduped in feed order). `read` never raises — a failed fetch returns
  `[]`, a feed with XML errors still yields whatever parsed.
- `crawl4ai_pages.py` — `Crawl4AiPageCrawler` → `PageCrawler`: one
  headless Chromium (`BrowserConfig(headless, text_mode)`) for the whole service, started
  and closed from the lifespan. `crawl_pages` / `crawl_articles` run `arun_many` (the
  article config adds `PruningContentFilter` for `fit_markdown` and keeps the HTML intact
  for the date cascade). Every result becomes a `FetchedPage` in `to_page` (same module) —
  Crawl4AI's own types stop here.
- `litellm_client.py` — `LiteLlmClient` → `CrawlLlm`: `litellm.acompletion` with the `llm` settings group (model
  string with provider prefix, key, base URL) and the `web_crawl` token limits /
  temperature. Prompts declare page content untrusted; answers are fence-stripped and
  validated into `ListingVerdict` / `DateGuess`; any failure is a WARNING and `None`.

Notes: all fetching adapters **never raise** — a failed crawl returns `None` / `[]` / the
pages that did succeed, logged at WARNING/ERROR, so callers fall back without a `try` of
their own. Both Crawl4AI wrappers run `verbose=False`: crawl4ai otherwise narrates every
fetch to stdout. The date resolver reads the *already fetched* article text — it never
crawls the page a second time.
