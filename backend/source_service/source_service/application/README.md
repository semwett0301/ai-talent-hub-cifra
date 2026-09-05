# application

Use-case / orchestration layer. Coordinates via **ports** (interfaces it defines and
infrastructure implements); depends on the shared `common` package (schemas +
entities) and on the service's own `source_service.domain` (web-news entities and
rules), never on concrete infra. Collaborators are injected by the composition
root (`deps.py`).

- `ports/` — the interfaces (Protocols) infra/services implement, grouped by domain like
  `services/`: `source/` (repository, registrar, collectors, publisher), `scraping/`
  (page fetcher, feed reader, browser page crawler with `FetchedPage`, the crawl's LLM
  port `CrawlLlm`).
- `dto/` — request/response DTOs (Pydantic) for the use cases.
- `services/` — use cases, grouped by domain: `source/` (`SourceService`,
  `SourceRegistry`), `scraping/` (`WebCrawl` and its stages), `article/`
  (`DateResolution`, `ArticleJudgement`). One class per module.
- `parse/` — pure text-in/structure-out logic (no I/O): link/page recognition for
  `SourceService`'s type auto-detection, article extraction (news-please) for
  `RssCollector`, and for the WEB crawl: date parsing, listing-page and article-page
  reading, body-container choice.

Notes: import ports from their subpackage (`application.ports.scraping`), not infra classes. `SourceRegistry` is
built in `deps.py` and started from `main.py`'s lifespan. Between the crawl services
articles travel as domain `Article`s and the contract is the status. `parse/` has no port of
its own — it's plain functions `SourceService` calls directly, not something
infrastructure implements.
