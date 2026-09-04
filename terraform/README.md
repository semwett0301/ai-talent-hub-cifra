# terraform

Oracle Cloud (OCI) infra + cloud-init. **No-domain / HTTP-by-IP** variant:
provisions **one Always-Free instance** (Docker + a `deploy` user + firewall). The
app is deployed **separately** via Docker Compose — Terraform does not run it.
Manual console setup: `../plans/oci-console-setup.md`. Full plan:
`../plans/oracle-cloud-migration.md`.

- `providers.tf` — `oracle/oci` provider (`~> 6.0`) + `backend "s3"` on **OCI Object
  Storage** (bucket `cifra-tfstate`, key `cifra/oci.tfstate`; region + endpoint passed
  at `init` via `-backend-config`, they're tenancy/region-specific).
- `variables.tf` — OCI access (`OCI_*`), deploy/app (`SSH_PUBLIC_KEY`, `APP_NAME`,
  `DEPLOY_USER`), and shape (`SHAPE`/`OCPUS`/`MEMORY_GB`, default A1.Flex 4/24).
- `network.tf` — VCN + internet gateway + route table + subnet + security list (22/80).
- `main.tf` — availability-domain + newest-Ubuntu lookups + `oci_core_instance`
  (flexible shape, public IP, cloud-init as base64 `user_data`).
- `outputs.tf` — `server_ipv4` (= instance `public_ip`), `ssh_command`, `app_url`.
- `cloud-init/` — first-boot prep: `deploy` user, `/opt/<app_name>`, **installs
  Docker**, opens port 80 in host iptables.
- `terraform.tfvars.example`, `backend.hcl.example` — copy + fill for local runs.

Notes: Always Free ARM (A1.Flex) can hit "Out of host capacity" — retry, change
region/AD, or fall back to `SHAPE=VM.Standard.E2.1.Micro` (x86, 1 GB). Images are
mostly multi-arch, so aarch64 is fine. Only ports 22/80 are open (security list +
host iptables). After apply, ship `docker-compose.yml` to `/opt/<app_name>` and
`docker compose up -d`.

## Inputs: local vs GitHub Actions

- **Local** — `terraform.tfvars` (copy `terraform.tfvars.example`) +
  `terraform init -backend-config=backend.hcl` (copy `backend.hcl.example`, set
  namespace/region) + `export AWS_ACCESS_KEY_ID/SECRET` (the OCI Customer Secret Key).
- **GitHub Actions** (`.github/workflows/deploy.yml`, `infra` job) — all inputs come
  from repo **Secrets** as `TF_VAR_*`; the S3 endpoint is built from
  `secrets.OCI_REGION` + repo **variable** `vars.OCI_NAMESPACE`.

Secrets/vars — repo → Settings → Secrets and variables → Actions:

| Name | Kind | Maps to |
|------|------|---------|
| `OCI_TENANCY_OCID` | secret | `TF_VAR_OCI_TENANCY_OCID` |
| `OCI_USER_OCID` | secret | `TF_VAR_OCI_USER_OCID` |
| `OCI_FINGERPRINT` | secret | `TF_VAR_OCI_FINGERPRINT` |
| `OCI_PRIVATE_KEY` | secret | `TF_VAR_OCI_PRIVATE_KEY` |
| `OCI_REGION` | secret | `TF_VAR_OCI_REGION` + S3 endpoint |
| `OCI_COMPARTMENT_OCID` | secret | `TF_VAR_OCI_COMPARTMENT_OCID` |
| `OCI_NAMESPACE` | **variable** | Object Storage namespace (S3 endpoint) |
| `TF_STATE_ACCESS_KEY` | secret | `AWS_ACCESS_KEY_ID` (Customer Secret Key) |
| `TF_STATE_SECRET_KEY` | secret | `AWS_SECRET_ACCESS_KEY` (Customer Secret Key) |
| `SSH_PUBLIC_KEY` | secret | `TF_VAR_SSH_PUBLIC_KEY` |
| `APP_NAME` | secret | `TF_VAR_APP_NAME` |
| `DEPLOY_USER` | secret | `TF_VAR_DEPLOY_USER` (default `deploy`) |

## Remote state (OCI Object Storage, S3-compatible)

Bucket `cifra-tfstate`, key `cifra/oci.tfstate`, endpoint
`https://<namespace>.compat.objectstorage.<region>.oraclecloud.com`. Bucket +
Customer Secret Key are created in the OCI console **before** `terraform init` (see
`../plans/oci-console-setup.md`). No state locking — don't run local and CI applies
at once.
