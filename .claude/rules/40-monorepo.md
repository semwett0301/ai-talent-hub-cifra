# Monorepo structure

uv workspace. A single shared package `common/` at the repo root (imported as
`common`) plus one package per service under `services/*`. The root
`pyproject.toml` **is** the `common` package and the workspace root.
`docker-compose.yml` sits at the root. Members glob: `services/*`.

- One shared library only — it's `common/` at the root. Do not reintroduce a
  `libs/` wrapper or a nested package dir.
- **Models live only in `common.models`.** Services never define tables.
- Shared code (config, db, schemas, LLM) goes in `common`; service dirs hold only
  that service's own logic.
- **No cross-service imports** — services share via `common`.
- Each service has its own top-level `app` package, its own `pyproject.toml`
  (depending on `common`), and its own `Dockerfile`.
- New service = create `services/<name>/` (copy `services/api` shape) and add a
  block to `docker-compose.yml`; the `services/*` glob picks it up automatically.
- One shared Postgres. When migrations are (re)introduced, use a single Alembic
  history and let only one service run `upgrade head` on startup.
- Run tooling from the root with uv: `uv sync --all-packages`, `uv run ...`,
  `uvx ruff@0.14.0 check .`.
