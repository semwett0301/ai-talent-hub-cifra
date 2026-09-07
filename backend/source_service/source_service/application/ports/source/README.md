# ports/source

Sources as records and as a running schedule, and the news they produce.

- `repositories.py` — `SourceRepository`: `list_all` / `get` / `list_enabled(type)` +
  create/update/delete over sources. Implemented by `SourceRepo`.
- `job_scheduler.py` — `JobScheduler` (`schedule`/`unschedule`, both idempotent) and the
  `PullRun` it calls: recurring per-source jobs addressed by source id, no job-id strings
  and no library in sight. Implemented by `ApSchedulerJobs`.
- `collectors.py` — `PullCollector` (`fetch`), `PushCollector` (`subscribe` /
  `unsubscribe`): the per-source-type "how to get news". Implemented in
  `infrastructure/collectors`.
- `publisher.py` — `NewsPublisher`: publishes `common.entities.news.NewsDTO`s to the bus.
  Implemented by `RabbitConnector`.
- `stored_news_index.py` — `StoredNewsIndex`: which of these URLs the shared `news` table
  already holds, so a collector re-crawls nothing. Returns the known subset instead of
  raising — a failed lookup means "nothing known", and the poll re-collects rather than
  dropping news. Implemented by `StoredNewsRepo`.

Notes: the repository method is `list_all` (not `list`) so the name doesn't shadow the
builtin `list[...]` used in return annotations. There is **no** registrar port: `SourceService`
takes `SourceRegistry` itself — both are application services in the same package, so a
protocol between them would invert nothing.
