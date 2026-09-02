# app

The `cifra-api` application package.

- `main.py` — FastAPI entrypoint: the `app` object plus `/` and `/health`.

Notes: add routers under `app/api/...` and mount them on `app` as endpoints grow.
