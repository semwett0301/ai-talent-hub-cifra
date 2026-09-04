# cloud-init

- `cloud-init.yaml.tftpl` — cloud-config rendered by `templatefile()` in `main.tf`
  and passed as base64 `user_data`. First boot **prepares the server only**: creates
  the `${deploy_user}` user with the SSH key, creates `/opt/<app_name>` owned by it
  (**first `runcmd` step**), **installs Docker** (+ compose plugin), and opens port
  80 in the host iptables.

Notes: template vars from `main.tf` — `deploy_user`, `ssh_public_key`, `app_dir`,
`hostname`. Unlike Timeweb, OCI images ship **without Docker**, so it's installed
here via `get.docker.com`. OCI Ubuntu images also block all but port 22 in local
iptables, so we explicitly `iptables -I INPUT ... --dport 80 ACCEPT` (the OCI
security list already allows 22/80 at the cloud level). It does **not** deploy the
app — you ship `docker-compose.yml` to `/opt/<app_name>` separately.

**Resilience:** the deploy dir is created **first** and nothing after uses `set -e`,
so a docker/iptables hiccup can't leave `/opt/<app_name>` uncreated (the deploy user
isn't a sudoer and can't create it under `/opt`). `bootcmd` stops `apt-daily` and
waits for the dpkg lock before the packages module. Keep `#cloud-config` as the
first line (required directive). Runs only on first boot.
