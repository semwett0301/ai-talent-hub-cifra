# terraform

DigitalOcean infra + cloud-init. **No-domain / HTTP-by-IP** variant: provisions **one
droplet** (Docker + a `deploy` user + UFW) with a reserved IP. The
app is deployed **separately** via Docker Compose — Terraform does not run it.
Manual console setup (one-time, before the first `init`): `../plans/digitalocean-setup.md`.

- `providers.tf` — `digitalocean/digitalocean` provider (`~> 2.40`, auth via the
  `DIGITALOCEAN_TOKEN` env var) + `backend "s3"` on **Spaces** (bucket `cifra-tfstate`,
  key `cifra/terraform.tfstate`, endpoint `ams3.digitaloceanspaces.com` — hardcoded,
  so `terraform init` needs no backend config).
- `variables.tf` — deploy/app (`SSH_PUBLIC_KEY`, `APP_NAME`, `DEPLOY_USER`,
  `SERVER_NAME`) and droplet (`REGION`/`SIZE`/`IMAGE`, default ams3 / s-2vcpu-4gb /
  ubuntu-24-04-x64).
- `main.tf` — `digitalocean_ssh_key` + `digitalocean_droplet` (cloud-init as
  `user_data`) + `digitalocean_reserved_ip`. No cloud firewall — the host gates itself.
- `outputs.tf` — `server_ipv4` (= the reserved IP), `ssh_command`, `app_url`.
- `cloud-init/` — first-boot prep: `deploy` user, `/opt/<app_name>`, UFW (22), Docker.
- `.gitignore` — keeps state/tfvars/plans out of git.

Inputs come from the **repo-root `.env`** as `TF_VAR_*` (see `../.env.example` and
the variable reference in `../README.md`) — there is no `terraform.tfvars`.

Notes: no DO cloud firewall, so the host is the only gate. UFW allows just 22; Docker
exposes nginx's 80 through its own iptables chain, which UFW does not filter — so
**every port Compose publishes is public**. Keep `ports:` on nginx only (postgres /
rabbitmq stay on `expose`). **Editing `cloud-init/` replaces the droplet** — `user_data` is immutable on
DO — but the reserved IP re-attaches to the new droplet, so `server_ipv4` is stable.
Data on the old droplet is lost; `/opt/<app_name>/.env` must be recreated by hand.
After apply, ship `docker-compose.yml` to `/opt/<app_name>` and `docker compose up -d`.

## Inputs: local vs GitHub Actions

- **Local run** — everything from the repo-root `.env`: `set -a; source ../.env; set +a`
  exports `TF_VAR_*` (inputs), `DIGITALOCEAN_TOKEN` (provider) and the Spaces keys
  (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`) for the state. For the SSH key
  itself: `TF_VAR_SSH_PUBLIC_KEY="$(cat ~/.ssh/deploy_key.pub)"`. Then
  `terraform init && terraform plan -out=tfplan && terraform apply tfplan`.
- **GitHub Actions** (`.github/workflows/deploy.yml`, `infra` job) — the `.env` is
  absent on the runner; all inputs come from repo **Secrets** injected as `TF_VAR_*`.
  The Secret ↔ `.env` key mapping is in `../README.md` → "GitHub Actions Secrets".

CI/CD lives in a single `deploy.yml`: the `infra` job runs `terraform apply` (only
when `terraform/**` changed, or on manual dispatch), then the `deploy` job ships the
app over SSH — reading the server IP from `terraform output` (Spaces state), so there's
no `SSH_HOST` secret. To expose more knobs (`SERVER_NAME`, `REGION`, `SIZE`) in CI,
add matching `TF_VAR_*` lines to the `infra` job.

## Remote state (DigitalOcean Spaces, S3-compatible)

Bucket `cifra-tfstate` in **ams3**, key `cifra/terraform.tfstate`. The bucket and a
Spaces access key are created in the DO console **before** `terraform init` (see
`../plans/digitalocean-setup.md`). Spaces has no state locking — don't run local and
CI applies at once. `.gitignore` blocks `*.tfvars` so a stray file can't be committed.
