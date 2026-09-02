# services

One package per deployable service.

- `api/` — the FastAPI dashboard/CRUD service.

Notes: each service has its own `app/` package, `pyproject.toml` (depends on
`common`), and `Dockerfile`. New service = copy `api/` and add a block to the root
`docker-compose.yml` (`services/*` is picked up automatically). No cross-service
imports.
