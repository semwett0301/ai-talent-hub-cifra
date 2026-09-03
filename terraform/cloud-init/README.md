# cloud-init

- `cloud-init.yaml.tftpl` — cloud-config template rendered by `templatefile()` in
  `main.tf`. First boot **prepares the server only**: installs the SSH key for
  both `root` and a `deploy` user (no sudo), waits for the Docker daemon, adds
  `deploy` to the docker group, configures UFW (22/80), and creates
  `/opt/<app_name>` owned by `deploy`.

Notes: Docker + Compose v2 come **pre-installed from the Timeweb "Docker" image**
(`data.twc_software.docker` in `main.tf`), not from this script — cloud-init only
waits until the daemon is ready. It does **not** deploy the app — you ship
`docker-compose.yml` to `/opt/<app_name>` and run it separately. `${...}` is
substituted by Terraform; keep `#cloud-config` as the first line (required
directive, not a comment). Runs only on first boot (`ignore_changes` on
`cloud_init`).
