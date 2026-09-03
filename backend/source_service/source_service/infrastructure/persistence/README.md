# persistence

Database persistence — the ORM schemas (tables) and the repositories over them.

- `schemas/` — SQLAlchemy ORM models (the `Source` table).
- `repositories/` — repository implementations (`SourceRepo`) of the application
  repository ports.

Notes: the shared `Base` + async session come from `common.core`. The migration
history for these tables lives in the `migrator` service, not here.
