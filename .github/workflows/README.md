# workflows

GitHub Actions.

- `backend.yml` — Ruff lint + format check on `backend/` (push/PR, path-filtered).
- `frontend.yml` — oxlint on `frontend/` (push/PR, path-filtered).
- `infra.yml` — Terraform `apply` of `terraform/`. Runs on `workflow_dispatch` and
  on push to `main` touching `terraform/**`. State lives in Timeweb S3. Needs
  secrets `TWC_TOKEN`, `TF_STATE_ACCESS_KEY`, `TF_STATE_SECRET_KEY` and variable
  `SSH_KEY_NAME`.
- `deploy.yml` — app release: rsync the repo to the server and
  `docker compose up -d --build` over SSH. Runs on `workflow_dispatch` and on push
  to `main` touching `backend/`, `frontend/`, `nginx/`, or `docker-compose.yml`.
  Needs secrets `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, `DEPLOY_PATH`
  (+ optional `SSH_PORT`). See `../../plans/ci-deploy-pipeline.md`.

Notes: CI workflows are path-filtered so a change runs only the relevant job.
`infra.yml` (server) and `deploy.yml` (app on it) are intentionally separate — a
code push redeploys the app without ever touching Terraform.
