# terraform

Timeweb Cloud infra (Terraform + cloud-init). **No-domain / HTTP-by-IP** variant:
provisions **one server** (Docker + a `deploy` user + firewall). The application
is deployed **separately** via Docker Compose — Terraform does not run it. See
`../plans/timeweb-terraform-cloudinit.md` for the walkthrough.

- `providers.tf` — Terraform + `timeweb-cloud/timeweb-cloud` provider (`~> 1.8`) +
  `backend "s3"` storing state in Timeweb S3 (`cifra-tfstate`).
- `variables.tf` — inputs (`SSH_PUBLIC_KEY`, server size/location, `APP_NAME`).
- `main.tf` — data lookups (configurator, Docker software) + `twc_ssh_key` +
  `twc_floating_ip` (public IPv4, bound at boot) + `twc_server`.
- `outputs.tf` — `server_ipv4`, `ssh_command`, `app_url` (http://IP).
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
  `terraform.tfvars.example`; set `SSH_PUBLIC_KEY` or
  `export TF_VAR_SSH_PUBLIC_KEY="$(cat deploy-key.pub)"`) plus `export TWC_TOKEN=...`
  and the S3 state keys (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`) in the shell.
- **GitHub Actions** (`.github/workflows/deploy.yml`, `infra` job) —
  `terraform.tfvars` is **not used** (it's gitignored, absent on the runner). All
  inputs come from repo **Secrets**, injected as `TF_VAR_*`.

Set them in **repo → Settings → Secrets and variables → Actions** (all Secrets):

| Name                  | Maps to                             | Required |
|-----------------------|-------------------------------------|----------|
| `TWC_TOKEN`           | provider token                      | yes      |
| `TF_STATE_ACCESS_KEY` | `AWS_ACCESS_KEY_ID` (S3 state)      | yes      |
| `TF_STATE_SECRET_KEY` | `AWS_SECRET_ACCESS_KEY` (S3 state)  | yes      |
| `SSH_PUBLIC_KEY`      | `TF_VAR_SSH_PUBLIC_KEY`             | yes      |
| `APP_NAME`            | `TF_VAR_APP_NAME`                   | yes      |
| `DEPLOY_USER`         | `TF_VAR_DEPLOY_USER` (default `deploy`)| no    |

CI/CD lives in a single `deploy.yml`: the `infra` job runs `terraform apply` (only
when `terraform/**` changed, or on manual dispatch), then the `deploy` job ships the
app over SSH — reading the server IP from `terraform output` (S3 state), so there's
no `SSH_HOST` secret. To expose more knobs (`SERVER_NAME`, `LOCATION`, size) in CI,
add matching `TF_VAR_*` lines to the `infra` job.

## Remote state (Timeweb S3)

State lives in the `cifra-tfstate` bucket (`backend "s3"` in `providers.tf`,
endpoint `s3.twcstorage.ru`, region `ru-1`). The bucket and its access/secret keys
must be created in the Timeweb panel **before** `terraform init`. Locally, export
`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`; in CI they come from the
`TF_STATE_ACCESS_KEY` / `TF_STATE_SECRET_KEY` secrets. Note: Timeweb S3 has no
state locking — don't run local and CI applies at the same time.
