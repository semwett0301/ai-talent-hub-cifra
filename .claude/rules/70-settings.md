# Settings

All configuration lives in **one place**: `backend/common/common/core/settings`.

- Read config only through `common.core.settings.settings` — never `os.environ`, never a
  `BaseSettings` / `.env` reader anywhere else (a service, a use case, an adapter).
- Settings are **grouped by concern**, one `SettingsTemplate` subclass per module in
  `settings/templates/` (`postgres`, `rabbit`, `web_crawl`, `llm`, …), aggregated by the
  root `Settings` as `settings.<group>.<field>`.
- **Adding a variable**: a field on the matching template; a new concern = a new template
  module + a field on `Settings` + a row in `templates/README.md`. Then declare it in the
  root `.env.example` and document it in the root `README.md` (name, meaning, default,
  secret or not).
- Variable names stay **flat** (`POSTGRES_HOST`, `WEB_CRAWL_DAYS`): a group sets
  `env_prefix` when all its variables share one, otherwise field name = variable name.
  Never introduce a nested delimiter.
- A use case that needs configuration takes **its group** (`WebCrawlSettings`), not the
  whole `Settings` and not loose scalars copied out of it. Derive per-run variants with
  `model_copy(update=…)` in the composition root (`deps.py`), not by mutating the singleton.
- Every template stays dependency-free within `common.core` (`logging` and `db` import it).
