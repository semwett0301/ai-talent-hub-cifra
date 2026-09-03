# services

Application services — use cases and background aggregators, one public class per
module (re-exported from `__init__.py`).

- `source_service.py` — `SourceService`: CRUD use-cases over the `SourceRepository`
  port.
- `scheduler_service.py` — `SchedulerService`: pull aggregator; injected publisher +
  collectors + source loaders (APScheduler).
- `subscription_service.py` — `SubscriptionService`: push aggregator; injected
  collectors + source loader.

Notes: collaborators are injected from the root `deps.py`; these depend on
`application.ports`, never on concrete infra. The aggregators are started from
`main.py`'s lifespan.
