# repositories

Repository implementations of the application repository ports — async query helpers
over SQLAlchemy.

- `source_repo.py` — `SourceRepo`: implements `SourceRepository` (`list_all` / `get`
  / `list_enabled(type)` + create/update/delete). **Opens a fresh session per call**
  (`async_session_factory`), so one repo serves both request handlers and the
  long-lived, concurrent background aggregators. Mutations commit; a `source` passed
  to update/delete is `merge`d into the fresh session first. Commits go through one
  module-level `_commit` that turns the `normalized_link` unique violation into
  `SourceAlreadyExistsError` (→ 409), the way `NpaRepo` does for `npa.url`.

- `stored_news_repo.py` — `StoredNewsRepo`: implements `StoredNewsIndex` with one
  `select(News.url)` per call. **Read-only** — the `news` table is written by
  `news_service`; this only asks which URLs are already there so `RssCollector` skips
  them before fetching article pages. Reading it here is the shared kernel (one DB, models
  in `common.schemas`), not a cross-service import. A query failure logs a warning and
  returns an empty set, so a DB blip re-collects instead of losing news.

Notes: both repos **inherit** their port (explicit conformance) and are re-exported from
`__init__.py`. Sessions come from `common.core.db`, a fresh one per call.
