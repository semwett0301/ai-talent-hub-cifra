# Baseline conventions

Starter rules — expand these as the team agrees on more.

- Monorepo layout & shared-code rules: see `40-monorepo.md`.
- Keep LLM and network I/O in services / `common.llm`; endpoints stay thin.
- Read config only through `common.core.config.settings`; never `os.environ`.
- Log via `common.core.logging.get_logger`; no `print`.
- Reuse enums from `common.models.enums`; don't duplicate string literals.
- Every model change goes through Alembic autogenerate + a reviewed migration.
- Never commit secrets: `.env`, `*.session`, API keys.
- No external API / LLM calls in tests or CI.
- Match the surrounding code's style; run `ruff` + `mypy` before committing.

## Commits

- Follow Conventional Commits — see `20-git.md`. Types: **`feat` / `fix` /
  `chore` / `refactor`** (also `docs` / `test` / `perf` / `style` when they fit).
- Format: `type(scope): subject`, e.g. `feat(ingestion): add Telegram collector`.
- Don't commit to `main` directly; branch + PR. Don't auto-commit unless asked.
