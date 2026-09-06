# common.core.settings

**Every setting in the project lives here**, split into groups. Nothing reads
`os.environ`; nothing declares its own `BaseSettings` elsewhere.

- `templates/` — one group per concern, each a `SettingsTemplate` (pydantic-settings)
  that reads its variables flat from the environment / repo-root `.env`:
  `app`, `postgres`, `rabbit`, `edge`, `sources`, `news`, `telegram`, `web_crawl`, `llm`.
  See `templates/README.md`.
- `settings.py` — `Settings`: the aggregate, one field per group
  (`settings.postgres.async_database_url`, `settings.web_crawl.days`,
  `settings.llm.llm_token()`), and the cached `settings` singleton (`get_settings()`).
- `__init__.py` — re-exports `settings`, `Settings`, `get_settings`, `ENV_FILE` and every
  group class, so a use case can type against one group (`WebCrawlSettings`) without
  seeing the rest.

Notes: `Settings` itself is a plain model — each group parses the environment when it is
built, so variable names never get a nested delimiter (`POSTGRES_HOST`, not
`POSTGRES__HOST`) and a group can be instantiated alone in tests
(`WebCrawlSettings(days=7)`). Adding a variable = a field on the matching template (or a
new template + a field on `Settings`), plus a line in the root `.env.example` and
`README.md`. `settings` is imported by `logging` and `db`, so this package must stay
dependency-free within `core`. Alembic uses `settings.postgres.sync_database_url`;
everything else the async one. `ENV_FILE` is resolved from this file's position in the
checkout and is `None` when the package sits too shallow for that (the dev overlay mounts
it at `/src/common`) — then only the process environment is read, which is what a
container wants anyway.
