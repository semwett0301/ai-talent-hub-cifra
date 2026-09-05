# cloud-init

- `cloud-init.yaml.tftpl` — cloud-config rendered by `templatefile()` in `main.tf`
  and passed as the droplet's `user_data`. First boot **prepares the server only**:
  creates the `${deploy_user}` user with the SSH key, creates `/opt/<app_name>` owned
  by it (**first `runcmd` step**), enables **UFW (22 only)**, and **installs Docker**
  (+ compose plugin).

Notes: template vars from `main.tf` — `deploy_user`, `ssh_public_key`, `app_dir`,
`hostname`. The plain `ubuntu-24-04-x64` image ships without Docker, so it's installed
via `get.docker.com`. UFW allows only 22: Docker-published ports (nginx's 80) go through
Docker's own `DOCKER` iptables chain, which UFW does not filter, so 80 stays reachable
without a UFW rule. There is no DO cloud firewall, so anything Compose publishes is
public — only nginx may have `ports:`. It does **not** deploy the app — you ship `docker-compose.yml` to `/opt/<app_name>`
separately.

**Resilience:** the deploy dir is created **first** and nothing after uses `set -e`,
so a Docker install hiccup can't leave `/opt/<app_name>` uncreated (the deploy user
isn't a sudoer and can't create it under `/opt`). `bootcmd` stops `apt-daily` and
waits for the dpkg lock before the packages module. Keep `#cloud-config` as the
first line (required directive) and the file **ASCII-only**: a non-ASCII byte (an em
dash in a comment) made DO's metadata hand cloud-init an unparseable YAML blob, and
the whole config was silently skipped. Runs only on first boot; **any edit replaces the
droplet** on the next apply.
