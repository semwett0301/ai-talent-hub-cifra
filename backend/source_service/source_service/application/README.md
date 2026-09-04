# application

Use-case / orchestration layer. Coordinates the domain via **ports** (interfaces it
defines and infrastructure implements); depends on `domain` only, never on concrete
infra. Collaborators are injected by the composition root (`deps.py`).

- `ports/` — the interfaces (Protocols) infra/services implement: repositories,
  collectors, publisher, registrar.
- `dto/` — request/response DTOs (Pydantic) for the use cases.
- `services/` — the use cases / aggregators (`SourceService`, `SchedulerService`,
  `SubscriptionService`, `SourceRegistry`), one class per module.

Notes: import ports (`application.ports`), not infra classes. The aggregators are
built in `deps.py` and started from `main.py`'s lifespan.
