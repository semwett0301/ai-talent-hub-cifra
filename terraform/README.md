# terraform

Timeweb Cloud infra (Terraform + cloud-init). **No-domain / HTTP-by-IP** variant:
provisions **one server** (Docker + a `deploy` user + firewall). The application
is deployed **separately** via Docker Compose — Terraform does not run it. See
`../plans/timeweb-terraform-cloudinit.md` for the walkthrough.

- `providers.tf` — Terraform + `timeweb-cloud/timeweb-cloud` provider (`~> 1.8`) +
  `backend "s3"` storing state in Timeweb S3 (`cifra-tfstate`).
- `variables.tf` — inputs (ssh key, server size/location, `app_name`).
- `main.tf` — data lookups (configurator, Docker software, ssh key) + `twc_server`.
- `outputs.tf` — server IP, ssh command, `app_url` (http://IP), root password.
- `cloud-init/` — first-boot server prep (Docker + Compose v2, `deploy` user,
  UFW 22/80, creates `/opt/<app_name>` ready for a compose project).
- `terraform.tfvars.example` — copy to `terraform.tfvars` and fill in.
- `.gitignore` — keeps state/tfvars/plans out of git.

Notes: pass the API token via `export TWC_TOKEN=...` and the S3 state keys via
`export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...` (never commit them). Run:
`terraform init && terraform plan -out=tfplan && terraform apply tfplan`. Only ports
22 and 80 are open. After apply, deploy the app: copy your `docker-compose.yml` to
`/opt/<app_name>` and `docker compose up -d`. Domain + HTTPS is a later step (see
the plan's section 7).

## Inputs: local vs GitHub Actions

Two ways to feed variables — they don't mix:

- **Local run** — values from `terraform.tfvars` (copy from
  `terraform.tfvars.example`) plus `export TWC_TOKEN=...` and the S3 state keys
  (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`) in the shell.
- **GitHub Actions** (`.github/workflows/infra.yml`) — `terraform.tfvars` is
  **not used** (it's gitignored, absent on the runner). Variables come from the
  repo's Secrets/Variables, injected as `TF_VAR_*`. Anything not set falls back to
  the `default` in `variables.tf`.

Set them in **repo → Settings → Secrets and variables → Actions**:

| Kind     | Name                  | Maps to                             | Required |
|----------|-----------------------|-------------------------------------|----------|
| Secret   | `TWC_TOKEN`           | provider token                      | yes      |
| Secret   | `TF_STATE_ACCESS_KEY` | `AWS_ACCESS_KEY_ID` (S3 state)      | yes      |
| Secret   | `TF_STATE_SECRET_KEY` | `AWS_SECRET_ACCESS_KEY` (S3 state)  | yes      |
| Variable | `SSH_KEY_NAME`        | `TF_VAR_ssh_key_name`               | yes      |
| Variable | `APP_NAME`            | `TF_VAR_app_name` (default `myapp`) | no       |

The infra workflow runs `terraform apply` — manually (workflow_dispatch) or on push
to `main` touching `terraform/**`. App releases are a separate workflow
(`deploy.yml`, over SSH) — see `../plans/ci-deploy-pipeline.md`. To expose more
knobs (`server_name`, `location`, size) in CI, add matching `TF_VAR_*` lines to
`infra.yml`.

## Remote state (Timeweb S3)

State lives in the `cifra-tfstate` bucket (`backend "s3"` in `providers.tf`,
endpoint `s3.twcstorage.ru`, region `ru-1`). The bucket and its access/secret keys
must be created in the Timeweb panel **before** `terraform init`. Locally, export
`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`; in CI they come from the
`TF_STATE_ACCESS_KEY` / `TF_STATE_SECRET_KEY` secrets. Note: Timeweb S3 has no
state locking — don't run local and CI applies at the same time.
