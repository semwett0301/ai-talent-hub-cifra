# workflows

GitHub Actions.

- `backend.yml` — Ruff lint + format check on `backend/` (push/PR, path-filtered).
- `frontend.yml` — oxlint on `frontend/` (push/PR, path-filtered).
- `deploy.yml` — CI/CD on `workflow_dispatch` and push to `main`, three jobs:
  1. `changes` — detects whether `terraform/**` was touched (dorny/paths-filter).
  2. `infra` — `terraform apply` (OCI, state in OCI Object Storage); runs only when
     `terraform/**` changed (or on manual dispatch). Builds the S3 `backend.hcl` from
     `secrets.OCI_REGION` + `vars.OCI_NAMESPACE` before `init`.
  3. `deploy` — reads the server IP from Terraform output, rsyncs the repo to
     `/opt/<APP_NAME>` (created at first boot by cloud-init), then
     `docker compose up -d --build`.
  Secrets: `OCI_TENANCY_OCID`, `OCI_USER_OCID`, `OCI_FINGERPRINT`, `OCI_PRIVATE_KEY`,
  `OCI_REGION`, `OCI_COMPARTMENT_OCID`, `TF_STATE_ACCESS_KEY`, `TF_STATE_SECRET_KEY`
  (OCI Customer Secret Key), `SSH_PUBLIC_KEY`, `SSH_PRIVATE_KEY`, `APP_NAME`, optional
  `DEPLOY_USER`. Variable: `OCI_NAMESPACE`. SSH port is fixed at 22.

Notes: CI workflows are path-filtered so a change runs only the relevant job. The
server host is not a secret — it lives in Terraform state and is resolved at deploy
time via `terraform output`. `infra` is skipped unless `terraform/**` changed, so a
code-only push redeploys the app without re-running Terraform.
