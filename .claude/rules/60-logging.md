# Logging

Logs are the only window into a running service — every **logical action** leaves a
trace, and library noise never drowns it.

## Log every logical action

Each step a human would name when describing what the system did gets exactly **one**
`INFO` line: message received, message published, source registered / unregistered,
scheduled / unscheduled, subscribed / unsubscribed, created / updated / deleted,
type detected, external resource fetched, infra connected / closed.

- Log **at the layer that owns the action**, once — the use-case logs "source created",
  the registry logs "source registering", the collector logs "post received", the
  publisher logs "news published". Never re-log the same fact one layer up.
- Log the **outcome**, not the intent, when only one matters; log both (start +
  result) for anything that can hang or partially fail (a batch, a crawl, a load).
- A skipped or no-op branch is also an action: say so and say why
  (`pull run skipped: id=%s (gone or disabled)`), don't return silently.

## Level policy

| Level | Use for |
|---|---|
| `INFO` | logical actions (above) — the default for business events |
| `WARNING` | degraded but handled: creds absent, chat not found, crawl failed, publish dropped |
| `ERROR` | the action failed and nothing recovered it |
| `DEBUG` | per-item detail inside a batch, payload-shaped noise |

`DEBUG=true` must stay readable: if a line fires per message *and* per batch, the
per-message one is `DEBUG` and the batch summary is `INFO`.

## Message format

- Lowercase `<subject> <verb-ed>: key=value key=value` — greppable and stable:
  `source created: id=%s type=%s link=%s`, `news published: exchange=%s items=%d`.
- **Always `%s` lazy args**, never f-strings in the log call.
- Identify the subject by `id` / `link` / `url` — a log line no one can trace back to
  a row is useless. Never log secrets (session strings, tokens, passwords).

## Keep libraries quiet

Third-party transport/protocol loggers (AMQP frames, MTProto updates, HTTP wire) are
capped at `INFO` in `NOISY_LOGGERS` (`domain.core.logging`) regardless of `settings.debug`.
Add a library there the moment its `DEBUG` output floods the log — cap it, don't
silence it, so connect/disconnect diagnostics survive.

Config via `settings` only; get loggers via `domain.core.logging.get_logger`; no `print`.
