# parsing

Adapters that discover structure on the open web with a third-party parser/crawler —
the only place in the service that imports `feedsearch_crawler`.

- `feedsearch_finder.py` — `FeedsearchRssFeedFinder` → `RssFeedFinder`: runs
  `feedsearch_crawler.search_async` over the site (a few pages deep, plus the usual feed
  paths) and returns the RSS feed URLs it found — Atom and JSON Feed are dropped, each URL
  once, in the library's score order. `find` never raises: a failed crawl is a WARNING and
  `[]`, and the library itself answers `[]` for an unreachable root.

Notes: the search ignores `robots.txt` (`RESPECT_ROBOTS = False`, like the crawl4ai
adapters) — news sites such as kommersant fence their feeds off behind it, and the
operator named the site explicitly. The finder is stateless (a session per call), so `deps.py` builds one per
`SourceService`. `feedsearch_crawler` narrates every parsed page at INFO, so it sits in
`CHATTY_LOGGERS` (`common.core.logging`), capped at WARNING.
