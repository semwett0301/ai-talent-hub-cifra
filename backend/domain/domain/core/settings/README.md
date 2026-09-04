# domain.core.settings

- `settings.py` — `Settings` (pydantic-settings, reads the repo-root `.env`; `ENV_FILE`
  is resolved relative to this file, six levels up) and the cached `settings`
  singleton (`get_settings()`). Holds every service's knobs — the Postgres / RabbitMQ
  URLs, the `*_api_prefix` values shared with nginx, the `news_*` batch settings
  `news_service` reads, and the Telegram credentials.
- `__init__.py` — re-exports `settings`, `Settings`, `get_settings`, `ENV_FILE`.

Notes: add a field to `Settings` for every new variable and declare it in the root
`.env.example` + `README.md`; never read `os.environ` directly. Blank values in `.env`
arrive as `""` — see `_blank_to_none` for the optional-int case.
