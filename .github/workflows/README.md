# workflows

GitHub Actions.

- `backend.yml` — Ruff lint + format check on `backend/` (push/PR, path-filtered).
- `frontend.yml` — oxlint on `frontend/` (push/PR, path-filtered).
- `deploy.yml` — CI/CD on `workflow_dispatch` and push to `main`, three jobs:
  1. `changes` — detects whether `terraform/**` was touched (dorny/paths-filter).
  2. `infra` — `terraform apply` (DigitalOcean, state in Spaces); runs only when `terraform/**`
     changed (or on manual dispatch). Creates the SSH key from `SSH_PUBLIC_KEY`.
  3. `deploy` — reads the server IP from Terraform output (S3 state, no `SSH_HOST`
     secret), waits until cloud-init has finished (`/var/lib/cloud/bootstrap-complete`,
     up to 10 min — a replaced droplet is `active` long before Docker is installed),
     rsyncs the repo to `/opt/<APP_NAME>`, then `docker compose up -d --build`.
  Secrets: `DIGITALOCEAN_TOKEN`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
  `SSH_PUBLIC_KEY`, `APP_NAME`, `SSH_PRIVATE_KEY`, and optional `DEPLOY_USER`
  (default `deploy`). SSH port is fixed at 22.

Notes: CI workflows are path-filtered so a change runs only the relevant job. The
server host is not a secret — it lives in Terraform state and is resolved at deploy
time via `terraform output`. `infra` is skipped unless `terraform/**` changed, so a
code-only push redeploys the app without re-running Terraform.
