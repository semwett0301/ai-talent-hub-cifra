# parse/extraction

Full article text from an already-fetched page, used by `RssCollector` for each feed entry.

- `article.py` — `ExtractedArticle` (title/text/published_at) + `extract_article(html, url)`:
  news-please's deterministic stack (newspaper4k + readability + date heuristics, no LLM).
  `None` (never raises) when nothing usable came out.

Notes: only `NewsPlease.from_html` is used, never `from_url`/`from_urls` — those go through
news-please's `SimpleCrawler`, which parks results in a class-level dict, so concurrent calls
silently return nothing. Fetching is the caller's job. The empty result is `{}`, detected with
`isinstance(_, dict)` — **not** `isinstance(_, NewsArticle)`: news-please loads that class
under a bare `NewsArticle` module name, so it never matches. It is blocking (lxml,
~0.2s/article) — on the event loop run it via `asyncio.to_thread`, as `RssCollector` does.
This is the only place in the service that imports `newsplease`.
