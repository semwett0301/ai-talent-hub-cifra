# common.core.logging

- `setup.py` — `configure_logging()` (call once at startup: level from
  `settings.debug`, one-line format) and `get_logger(name)`. Caps `NOISY_LOGGERS`
  (aio_pika/aiormq/pamqp, pyrogram, httpx, urllib3, charset_normalizer, newspaper,
  readability) at INFO so `DEBUG=true` doesn't drown business logs in AMQP frames,
  MTProto updates and extractor DOM scoring; `CHATTY_LOGGERS` (newsplease and feedsearch_crawler, which
  narrate every article or crawled page at INFO) are capped at WARNING.
- `__init__.py` — re-exports the two functions and both tuples.

Notes: rules in `.claude/rules/60-logging.md` — one INFO line per logical action,
`%s` lazy args, no secrets. Add a library to the caps the moment it floods the log.
