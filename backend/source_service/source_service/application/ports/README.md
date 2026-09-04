# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). Re-exported from `__init__.py`.

- `collectors.py` — `PullCollector` (`fetch`), `PushCollector` (`subscribe`/
  `unsubscribe`).
- `repositories.py` — `SourceRepository`: `list_all` / `get` / `list_enabled(type)` +
  create/update/delete over sources.
- `publisher.py` — `NewsPublisher`: publishes `NewsItem`s to the bus.

Notes: ports reference the `domain.schemas` shapes (`Source`, `NewsItem`) directly.
The repository method is `list_all` (not `list`) so the name doesn't shadow the
builtin `list[...]` used in return annotations.
