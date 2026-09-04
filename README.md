# AI Analytical Center (Cifra Hackathon)

An AI-powered intelligence hub that automatically **collects, structures, and
summarizes industry news** in a single interface, with full user control over
sources and content.

Built for PR/GR teams who otherwise spend 3–4 hours a day manually monitoring
media, regulators, and Telegram channels.

## What it does

- **Collect** publications from media (RSS), regulator websites, and Telegram.
- **Summarize** with an LLM: short summary, key entities, category, priority.
- **Dashboard** with filtering and search, linking to the original.
- **User control**: add/edit/delete sources; edit or hide articles; add items
  manually.

## Structure

- `backend/` — Python (uv workspace): `common` shared lib + `source_service`
  (FastAPI) + `migrator` (Alembic), as sibling packages. Services follow **onion
  architecture** (domain → application → infrastructure → api, wired in `deps.py`);
  see `backend/README.md`.
- `frontend/` — React SPA (Vite, TypeScript, React Router).
- `nginx/` — edge: builds the SPA, serves it static, proxies `/api`; the only
  service exposed to the host.
- `docker-compose.yml` — nginx (public) + api + postgres (internal).

## Run

```bash
cp .env.example .env           # one file for the whole project, see below
docker compose up --build -d   # everything, reachable at http://localhost/
```

Local dev: backend `cd backend && uv run uvicorn source_service.main:app --reload --app-dir source_service`;
frontend `cd frontend && npm install && npm run dev`.

### Migrations

The `migrator` service owns the single Alembic history for the shared DB. Compose
runs `alembic upgrade head` once at startup; DB-backed services wait for it.

```bash
cd backend/migrator                                            # run from here
uv run alembic -c alembic.ini upgrade head                     # apply migrations
uv run alembic -c alembic.ini revision --autogenerate -m "msg" # after a model change
```

Autogenerate imports each service's models (listed in `SERVICE_MODEL_MODULES` in
`migrations/autogenerate.py`) to diff against the DB — so run it via `uv` where the whole
workspace is installed, then review the emitted revision. `upgrade` never reads
models, so the shipped migrator image carries no service packages. Adding a
service's first table: add the service to the `autogen` dependency group in
`migrator/pyproject.toml` and append its models module to `SERVICE_MODEL_MODULES`.
Each service ships a uniquely named package (e.g. `source_service`), so all coexist.
See `backend/migrator/README.md`.

## Environment variables

**One file for everything: the root `.env`.** Backend, frontend, nginx, Compose,
Terraform and the deploy workflow all read from it — there is no per-folder
`.env.example` and no `terraform.tfvars`.

```bash
cp .env.example .env      # then fill in the blanks
```

`.env` is gitignored, and the deploy job explicitly excludes it from the rsync —
on the server it is created once by hand in `/opt/<APP_NAME>/`. In CI the same
values live as **GitHub Actions Secrets** (mapping table at the end).

How each consumer picks it up:

- **Backend** — `common.settings.Settings` loads the repo-root `.env` by absolute
  path, so `uv run …` works from any directory. Never read `os.environ` directly.
- **Compose** — loads the root `.env` automatically for `${VAR}` substitution, and
  hands each service only the variables it needs (so infra/deploy secrets never
  enter an application container).
- **Frontend** — `VITE_*` are baked into the bundle at **build** time; Compose
  passes them to the nginx image as build args.
- **Terraform** — reads `TF_VAR_*` (→ `terraform/variables.tf`) plus the provider
  and state credentials. Locally: `set -a; source .env; set +a; terraform apply`.

### App (backend)

| Variable | Meaning | Default | Secret |
|---|---|---|---|
| `APP_NAME` | Service display name (FastAPI title, logs). | `AI Analytical Center` | no |
| `ENVIRONMENT` | `local` / `staging` / `production`. | `local` | no |
| `DEBUG` | Verbose logging and debug behaviour. | `true` | no |
| `SECRET_KEY` | App signing key. Change outside local. | `change-me-in-production` | **yes** |

### Postgres

| Variable | Meaning | Default | Secret |
|---|---|---|---|
| `POSTGRES_HOST` | DB host. `localhost` for local dev; Compose overrides it to `postgres`. | `localhost` | no |
| `POSTGRES_PORT` | DB port. | `5432` | no |
| `POSTGRES_USER` | Role used by services **and** by the `postgres` container itself. | `cifra` | no |
| `POSTGRES_PASSWORD` | Its password (same both sides — they must match). | `cifra` | **yes** |
| `POSTGRES_DB` | Database name. | `cifra` | no |
| `DATABASE_URL` | Full async DSN; overrides the five parts above. Commented out by default. | derived | **yes** |

### RabbitMQ

| Variable | Meaning | Default | Secret |
|---|---|---|---|
| `RABBITMQ_URL` | AMQP connection URL. Compose overrides it to the internal `rabbitmq` host. | `amqp://guest:guest@localhost:5672/` | **yes** |
| `NEWS_EXCHANGE` | Exchange collected news is published to. | `news` | no |

### Edge routing

| Variable | Meaning | Default | Secret |
|---|---|---|---|
| `SOURCES_API_PREFIX` | The nginx location `source_service` is mounted under, and the same value as FastAPI's `root_path` (so `/docs` and `openapi.json` resolve behind the proxy). Consumed by **both** containers — change it here only. | `/api/sources` | no |

### Frontend (build time)

| Variable | Meaning | Default | Secret |
|---|---|---|---|
| `VITE_API_BASE_URL` | Base path for API calls from the SPA. Same-origin by default — nginx proxies `/api`. | `/api` | no — **ships to the browser** |

### Telegram

Leave all three empty and the collector degrades to a no-op (it logs
`telegram creds absent; collector disabled` at startup) — the service still boots.

| Variable | Meaning | Default | Secret |
|---|---|---|---|
| `TELEGRAM_API_ID` | MTProto app id from https://my.telegram.org. | empty | **yes** |
| `TELEGRAM_API_HASH` | MTProto app hash from the same page. | empty | **yes** |
| `TELEGRAM_SESSION` | Exported **kurigram/pyrogram** session string of a pre-authorized user account (not interchangeable with a Telethon `StringSession`). Equivalent to full access to that account — use a dedicated one. | empty | **yes** |

### Terraform — provider and remote state

| Variable | Meaning | Default | Secret |
|---|---|---|---|
| `TWC_TOKEN` | Timeweb Cloud API token for the `twc` provider. | empty | **yes** |
| `AWS_ACCESS_KEY_ID` | Access key for the S3 state bucket (`cifra-tfstate`, Timeweb S3). | empty | **yes** |
| `AWS_SECRET_ACCESS_KEY` | Its secret key. Timeweb S3 has no state locking — never run a local and a CI apply at once. | empty | **yes** |

### Terraform — inputs (`TF_VAR_*`)

| Variable | Meaning | Default | Secret |
|---|---|---|---|
| `TF_VAR_SSH_PUBLIC_KEY` | Public key (OpenSSH format) uploaded to Timeweb and installed for `root` + the deploy user. | empty | **yes** |
| `TF_VAR_APP_NAME` | Project slug: deploy dir `/opt/<name>`, hostname, Compose project name. | `cifra` | no |
| `TF_VAR_DEPLOY_USER` | Non-root user created for SSH/deploy. | `deploy` | no |
| `TF_VAR_SERVER_NAME` | Server display name in the Timeweb panel. | `cifra-prod` | no |
| `TF_VAR_LOCATION` | `ru-1` (spb), `ru-2` (nsk), `ru-3` (msk), `de-1` (fra), `kz-1`, `nl-1`. | `ru-1` | no |
| `TF_VAR_AVAILABILITY_ZONE` | Must match the location (`ru-1`→`spb-3`, `ru-2`→`nsk-1`, `ru-3`→`msk-1`, `de-1`→`fra-1`, `kz-1`→`ala-1`, `nl-1`→`ams-1`). | `spb-3` | no |
| `TF_VAR_OS_NAME` / `TF_VAR_OS_VERSION` | OS family/version for the image lookup; must exist paired with the Docker software image. | `ubuntu` / `24.04` | no |
| `TF_VAR_CPU` | vCPU count (configurator minimum 2). | `2` | no |
| `TF_VAR_RAM_MB` | RAM in MB, multiple of 1024. | `4096` | no |
| `TF_VAR_DISK_MB` | System disk in MB: 40960–2048000, step 5120. | `40960` | no |

### Deploy

| Variable | Meaning | Default | Secret |
|---|---|---|---|
| `SSH_PRIVATE_KEY` | Private key matching `TF_VAR_SSH_PUBLIC_KEY`, used by the `deploy` job to rsync and restart Compose. CI only — no local use. | empty | **yes** |

The server host is deliberately **not** a variable: the deploy job reads it from
Terraform state via `terraform output -raw server_ipv4`.

### GitHub Actions Secrets

`deploy.yml` expects these names — a few differ from the `.env` key, since
Terraform and the AWS SDK read fixed variable names:

| GitHub Secret | `.env` key | Used by |
|---|---|---|
| `TWC_TOKEN` | `TWC_TOKEN` | `infra` — provider |
| `TF_STATE_ACCESS_KEY` | `AWS_ACCESS_KEY_ID` | `infra`, `deploy` — S3 state |
| `TF_STATE_SECRET_KEY` | `AWS_SECRET_ACCESS_KEY` | `infra`, `deploy` — S3 state |
| `SSH_PUBLIC_KEY` | `TF_VAR_SSH_PUBLIC_KEY` | `infra` |
| `SSH_PRIVATE_KEY` | `SSH_PRIVATE_KEY` | `deploy` |
| `APP_NAME` | `TF_VAR_APP_NAME` | `infra`, `deploy` (`/opt/<APP_NAME>`) |
| `DEPLOY_USER` | `TF_VAR_DEPLOY_USER` | `infra`, `deploy` (optional, default `deploy`) |

Application secrets (`SECRET_KEY`, `POSTGRES_PASSWORD`, `TELEGRAM_*`) are **not**
used by the workflow today — the app reads them from the `.env` that lives on the
server. Move them into Secrets and render the file in the `deploy` job when that
should be automated.

## Commit conventions

[Conventional Commits](https://www.conventionalcommits.org/): `type(scope): subject`.
Types: `feat`, `fix`, `chore`, `refactor` (also `docs`, `test`, `perf`, `style`).
Branch + PR rather than committing to `main`. Full rules in
`.claude/rules/20-git.md`.

## Out of scope (per the brief)

Production-scale load, additional modalities, and information security.
