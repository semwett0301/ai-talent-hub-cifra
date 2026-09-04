# services

Application services — use cases and background aggregators, one public class per
module (re-exported from `__init__.py`).

- `source_service.py` — `SourceService`: CRUD use-cases over the `SourceRepository`
  port.
- `scheduler_service.py` — `SchedulerService`: pull aggregator; injected publisher +
  collectors + `SourceRepository` (APScheduler).
- `subscription_service.py` — `SubscriptionService`: push aggregator; injected
  collectors + `SourceRepository`.

Notes: collaborators are injected from the root `deps.py` as ports (interfaces),
never bare callables or concrete infra. The aggregators load sources through the
injected `SourceRepository` (`deps` passes a `SourceRepo`, which opens a session per
call — safe for these long-lived, concurrent services). Started from `main.py`'s
lifespan.
