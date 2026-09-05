# infrastructure/scheduling

The `JobScheduler` port on a concrete scheduler. Everything APScheduler-shaped stops here.

- `apscheduler_jobs.py` — `ApSchedulerJobs`: `schedule(source_id, seconds, run)` /
  `unschedule(source_id)` over an `AsyncIOScheduler`. Turns a source id into a job id
  (`src-<uuid>`), so no caller ever sees one; `replace_existing=True` makes rescheduling
  idempotent and `unschedule` returns quietly for an unknown source.

Notes: owns `start`/`shutdown`, driven from `main.py`'s lifespan alongside the other infra
clients — `SourceRegistry` has no lifecycle of its own.
