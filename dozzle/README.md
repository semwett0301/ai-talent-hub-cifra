# dozzle

Config dir of the Dozzle container-log viewer (mounted read-only at `/data`).

- `users.yml` — **gitignored**: the users Dozzle's `simple` auth provider accepts at
  `http://<host>/logs/`, bcrypt-hashed. Generated from `LOGS_USER` / `LOGS_PASSWORD`:
  - **on the server** by the `deploy` job (`.github/workflows/deploy.yml`) after every
    rsync — hashes the GitHub Secrets on the runner with `dozzle generate` and scp's the
    file to `/opt/<APP_NAME>/dozzle/users.yml`;
  - **locally** by hand, once, from the root `.env`:

    ```bash
    set -a; source .env; set +a
    docker run --rm amir20/dozzle:v10.9.2 generate "$LOGS_USER" --password "$LOGS_PASSWORD" \
      --email "$LOGS_USER@localhost" --name "$LOGS_USER" > dozzle/users.yml
    ```

  Without the file Dozzle refuses to start and `/logs/` answers 502 — fail closed.

Notes: Dozzle itself is configured in `docker-compose.yml` (`DOZZLE_BASE` =
`LOGS_PREFIX`, `DOZZLE_AUTH_PROVIDER=simple`, `DOZZLE_FILTER` on this compose project).
Sessions are JWT cookies signed with a key generated at container start, so a restart
logs everyone out. Anyone who can log in sees every container's logs **and env** (the
docker socket exposes them) — treat the password as a secret.
