# ports/scraping

Reaching pages, feeds and sites, and the crawl's language model.

- `page_fetcher.py` — `PageFetcher` (`fetch`): a URL's raw body (page HTML, feed XML) over
  plain HTTP, for `RssCollector`'s feeds and article pages. Implemented by
  `Crawl4AiPageFetcher`.
- `rss_feed_finder.py` — `RssFeedFinder` (`find`): every RSS feed URL a site address leads
  to — advertised in its pages or served at well-known paths — for `SourceService`'s type
  auto-detection. Implemented by `FeedsearchRssFeedFinder`.
- `feed_reader.py` — `FeedReader` (`read`) + its return shape `FeedEntry`: one RSS/Atom feed
  downloaded and parsed for `RssCollector`. Implemented by `FeedparserFeedReader`.
- `page_crawler.py` — `PageCrawler`: the browser. `crawl_page` / `crawl_pages` /
  `crawl_articles` return `FetchedPage`s (url, final_url, html, markdown, title, internal
  `PageLink`s, metadata) — **the only form a page takes outside the adapter**. Implemented
  by `Crawl4AiPageCrawler`.
- `crawl_llm.py` — `CrawlLlm`: the two questions the crawl asks a model —
  `classify_listing(url, snapshot)` for `HubDiscovery`, `resolve_publication_date(url,
  text)` for `DateResolution`. Implemented by `LiteLlmClient`.
- `listing_verdict.py` — `ListingVerdict`, the answer to the first question.
- `date_guess.py` — `DateGuess`, the answer to the second; its field descriptions double as
  the model's JSON-schema instructions.

Notes: every fetching port **never raises** — a failure is `None` / `[]` / a missing page
plus a WARNING at the adapter, so callers need no `try` of their own. `CrawlLlm` returns
`None` on a failed or invalid answer; the caller then treats the page as "not a listing"
or "no date". One adapter, one port: `PageCrawler` and `CrawlLlm` are not split by the
service that calls them.
