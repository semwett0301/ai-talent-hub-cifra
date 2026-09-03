# ports

The interfaces application depends on and infrastructure implements (`Protocol`, so
impls match structurally — no inheritance needed). Re-exported from `__init__.py`.

- `collectors.py` — `PullCollector` (`fetch`), `PushCollector` (`subscribe`/
  `unsubscribe`).
- `repositories.py` — `SourceRepository`: persistence operations over sources.
- `publisher.py` — `NewsPublisher`: publishes `NewsItem`s to the bus.

Notes: ports reference the ORM `Source` schema directly (pragmatic — no separate
domain entity for Source). `repositories.py` uses `from __future__ import annotations`
so the `list()` method name doesn't shadow the `list[...]` return annotations.
