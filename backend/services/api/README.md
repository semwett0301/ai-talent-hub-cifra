# cifra-api

FastAPI dashboard/CRUD service (skeleton: `/`, `/health`).

- `app/` — application package (entrypoint + routers).
- `Dockerfile` — image build (context `./backend`).
- `pyproject.toml` — package `cifra-api`, depends on `common`.

Notes: run `uv run uvicorn app.main:app --reload` from here. Runs internally in
Docker; nginx proxies `/api/` to it. Keep endpoints thin — logic/I-O in `common`.
