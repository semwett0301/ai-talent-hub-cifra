# cloud-init

- `cloud-init.yaml.tftpl` — cloud-config template rendered by `templatefile()` in
  `main.tf`. First boot **prepares the server only**: installs the SSH key for
  both `root` and the `${deploy_user}` user (no sudo), creates `/opt/<app_name>`
  owned by that user (**first `runcmd` step**), waits for the Docker daemon, adds
  the user to the docker group, and configures UFW (22/80).

Notes: template vars passed from `main.tf` — `deploy_user` (`var.DEPLOY_USER`),
`ssh_public_key`, `app_dir`, `hostname`. Docker + Compose v2 come **pre-installed
from the Timeweb "Docker" image** (`data.twc_software.docker` in `main.tf`), not
from this script — cloud-init only waits until the daemon is ready. It does **not**
deploy the app — you ship `docker-compose.yml` to `/opt/<app_name>` and run it
separately. `${...}` is substituted by Terraform; keep `#cloud-config` as the first
line (required directive, not a comment).

**Resilience (why it's shaped this way):** the deploy dir is created **first** and
nothing after it uses `set -e`, so a docker/ufw hiccup can't leave `/opt/<app_name>`
uncreated (that was the `rsync mkdir … Permission denied` bug — the deploy user
can't create it). `bootcmd` stops the `apt-daily` timers and waits for the dpkg
lock before the packages module, so cloud-init's apt run doesn't race them and
corrupt the cache. cloud-init runs **only on first boot**; `cloud_init` is no longer
in `main.tf`'s `ignore_changes`, so editing this template **reprovisions (replaces)
the server** on the next `terraform apply`.
