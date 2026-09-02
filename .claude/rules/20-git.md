# Git Conventions (project)

Our own rules — override the base set. Applies to every commit in this repo.

## Commit rules

- Do not commit automatically unless explicitly asked.
- Before committing, make sure the code runs: `ruff check app` and `pytest -q`
  must pass.
- Do not commit straight to `main`. Branch first (`feat/...`, `fix/...`), then
  open a PR. Commit secrets never (`.env`, `*.session`, API keys).

## Commit message format

Conventional Commits:

```
<type>(<scope>): <subject>
```

- Space after the colon; subject in imperative mood, lower-case, no trailing dot.
- `scope` is optional but encouraged (e.g. `api`, `ingestion`, `db`, `workers`).

### Allowed types

Core four — use these for almost everything:

| type       | Purpose                                              |
|------------|------------------------------------------------------|
| `feat`     | New feature / user-visible capability                |
| `fix`      | Bug fix                                               |
| `chore`    | Tooling, deps, config, CI, housekeeping (no app logic)|
| `refactor` | Code change that neither fixes a bug nor adds a feature|

Also allowed when they fit better: `docs`, `test`, `perf`, `style`.

### Body

Use a bulleted list when there is more than one meaningful change:

```
feat(ingestion): add Telegram channel collector

- Read public channels via Telethon (graceful when creds absent)
- Dedupe by (source_id, url) before persisting
- Wire collector into the COLLECTORS registry
```

## Examples

```
feat(api): add article search and priority filter
fix(db): correct nullslast ordering on published_at
chore(deps): pin crawl4ai to 0.4.24
refactor(services): extract summarization JSON parsing into _parse
```
