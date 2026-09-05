# ports/source

Sources as records and as a running schedule, and the news they produce.

- `repositories.py` — `SourceRepository`: `list_all` / `get` / `list_enabled(type)` +
  create/update/delete over sources. Implemented by `SourceRepo`.
- `registrar.py` — `SourceRegistrar` (`register`/`unregister`): reconciles one source to
  the runtime. Implemented by `SourceRegistry`; injected into `SourceService` so CRUD
  stays live.
- `collectors.py` — `PullCollector` (`fetch`), `PushCollector` (`subscribe` /
  `unsubscribe`): the per-source-type "how to get news". Implemented in
  `infrastructure/collectors`.
- `publisher.py` — `NewsPublisher`: publishes `common.entities.news.NewsDTO`s to the bus.
  Implemented by `RabbitConnector`.

Notes: the repository method is `list_all` (not `list`) so the name doesn't shadow the
builtin `list[...]` used in return annotations.
