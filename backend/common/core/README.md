# common.core

- `config.py` — `Settings` (pydantic-settings, reads `.env`) + `settings` singleton.
- `logging.py` — `configure_logging()` + `get_logger()` over stdlib `logging`.

Notes: read config only via `settings` (never `os.environ`); log via `get_logger`
(no `print`). Add new settings as fields on `Settings`.
