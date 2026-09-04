# workflows

GitHub Actions.

- `backend.yml` — Ruff lint + format check on `backend/` (push/PR, path-filtered).
- `frontend.yml` — oxlint on `frontend/` (push/PR, path-filtered).
- `deploy.yml` — CI/CD on `workflow_dispatch` and push to `main`, three jobs:
  1. `changes` — detects whether `terraform/**` was touched (dorny/paths-filter).
  2. `infra` — `terraform apply` (Timeweb, S3 state); runs only when `terraform/**`
     changed (or on manual dispatch). Creates the SSH key from `SSH_PUBLIC_KEY`.
  3. `deploy` — reads the server IP from Terraform output (S3 state, no `SSH_HOST`
     secret); **only when `infra` ran** (terraform changed / manual dispatch) waits
     for first-boot `cloud-init` so the `/opt/<APP_NAME>` deploy dir exists and is
     owned by `DEPLOY_USER`; then rsyncs the repo there and `docker compose up -d
     --build`.
  Secrets: `TWC_TOKEN`, `TF_STATE_ACCESS_KEY`, `TF_STATE_SECRET_KEY`,
  `SSH_PUBLIC_KEY`, `APP_NAME`, `SSH_PRIVATE_KEY`, and optional `DEPLOY_USER`
  (default `deploy`). SSH port is fixed at 22.

Notes: CI workflows are path-filtered so a change runs only the relevant job. The
server host is not a secret — it lives in Terraform state and is resolved at deploy
time via `terraform output`. `infra` is skipped unless `terraform/**` changed, so a
code-only push redeploys the app without re-running Terraform.
