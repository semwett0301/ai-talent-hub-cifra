# backend

All Python code, as one uv workspace.

- `common/` — shared library, imported as `common`.
- `services/` — one package per deployable service (e.g. `api`).
- `pyproject.toml` — workspace root **and** the `common` package (deps + ruff/mypy/pytest config).
- `uv.lock` — locked versions (committed).
- `.env.example` — settings template → copy to `.env`.

Notes: run uv from here (`uv sync --all-packages`). This dir doubles as the
`common` package. Models live only in `common.models`; services never import each
other (share via `common`).
