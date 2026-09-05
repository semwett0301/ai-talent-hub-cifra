# domain (source_service)

The service's own domain layer: the web-news entities and the pure rules about them.
No I/O, no Crawl4AI, no LLM, no knowledge of the pipeline order — `application/web_crawl`
orchestrates these, `infrastructure` feeds them. The shared kernel is the top-level
`common` package (`NewsDTO`, ORM schemas, settings): that holds what crosses service
boundaries; this holds what only this service reasons about.

- `article/` — the `Article` aggregate: the entity at the root, its sub-models in
  `model/` (`ArticleContent`, `PublicationDate`, status enums), its rules in `rules/`
  (`ARTICLE_SCORER`, `FreshnessWindow`).
- `hub/` — the `Hub` aggregate, same shape: `hub.py`, `model/` (`HubOrigin`), `rules/`
  (`HUB_SCORER`).
- `site/` — the `Site` aggregate: the web source a crawl runs against; `owns(url)` is the
  same-site rule.
- `scoring/` — the generic mechanism only: `model/` (`ScoreRule[T]`, `Score`),
  `scorer.py` (`RuleScorer[T]`) and `terms.py` — the URL vocabulary that belongs to
  neither entity. Entity-specific vocabulary lives with the entity.
- `urls.py` — `normalize_url` (tracking params, slashes, case), `host_matches`,
  `listing_identity` (pagination variants are one hub), `is_pagination_url`, `path_depth`.
- `__init__.py` — re-exports the entities, enums and scorers; import from
  `source_service.domain`, reach into `domain.urls` for the URL helpers.

Notes: identity is a property of the entity (`Article.identity`, `Hub.identity`), so dedupe
never recomputes keys by hand. One entity per subpackage — the entity module at its root, `model/` for what it is
made of, `rules/` for what judges it; one class per module. Shared mechanism in
`scoring/`, shared vocabulary only when it is really about neither entity. Scores are computed on demand
from the entity, never stored on it, so nothing can carry a stale number. Thresholds are
the use case's, not the domain's — and so is *how* a value is obtained: parsing a printed
date (`application/parse/dates.py`) and the date-extraction techniques (`DateSource` in
`application/parse/article_page.py`) are the use case's; the domain only keeps the
result and its provenance label.
