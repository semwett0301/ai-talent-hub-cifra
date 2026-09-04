# Project instructions

These are project requirements. User instructions take precedence when they
explicitly conflict with this file.

## Baseline conventions

- Keep LLM and network I/O in services or `domain.llm`; endpoints stay thin.
- Read configuration only through `domain.core.settings.settings`; never use
  `os.environ` directly.
- Log through `domain.core.logging.get_logger`; do not use `print`.
- Reuse enums from `domain.entities.news`; do not duplicate string literals.
- Every model change goes through Alembic autogenerate and a reviewed migration.
- Never commit secrets: `.env`, `*.session`, or API keys.
- Do not make external API or LLM calls from tests or CI.
- Follow these requirements when working with legacy code; do not reproduce an
  existing pattern that conflicts with them.

## Code quality and design

- When changing old code, refactor the touched area to these requirements while
  preserving behavior. If this cascades across more than three files, explain
  the plan before proceeding.
- A function is at most 30 lines and a file at most 300 lines, excluding blank
  lines and comments. Split by responsibility when necessary.
- Keep nesting to three levels or fewer, use early returns, and accept no more
  than four function parameters; use an object parameter otherwise.
- Delete unused and commented-out code. Replace magic numbers and strings with
  named constants.
- Group small logical blocks with blank lines. Use at most one comment line per
  block; prefer clear names and extracted functions to explanatory comments.
- A class-centered module is ordered: module docstring, imports, constants,
  free utilities, then the class.
- Use semantic names. Avoid `data1`, `temp`, `info`, `obj`, `result`, and
  `item` except as loop variables. Boolean names start with `is`, `has`,
  `can`, or `should`; functions start with a verb; event handlers with
  `handle`; constants use `ALL_CAPS_SNAKE_CASE`.
- Keep a single responsibility per function and domain per file. Dependencies
  flow UI → business logic → data layer; do not reverse that flow.
- Communicate through interfaces or protocols. A port implementation inherits
  its `Protocol`; inject a named interface, never a bare callable, lambda, or
  concrete collaborator when a port exists.
- Prefer composition unless there is a clear is-a relationship.
- Validate defensively only at system boundaries. Catch specific exceptions,
  handle async failures, and wrap only the operations that may fail.
- Solve the requested problem. Do not add abstractions, options, utilities, or
  layers for hypothetical needs.

## Python

- Follow PEP 8 and use ruff for formatting and linting.
- Add type annotations to all public function parameters and return values.
- Use `pathlib.Path`, f-strings, `X | None`, built-in collection generics, and
  `TypeAlias` or `TypedDict` for complex types.
- Use `Protocol` rather than an ABC for structural subtypes.
- Use `PascalCase` for classes, `snake_case` for functions and variables, and
  `UPPER_SNAKE_CASE` for constants.
- Class members are private (`__name`) unless subclasses truly need protected
  access (`_name`); module-level private names use one leading underscore.
- Catch specific exceptions and chain failures with `raise ... from error`.
  Never use a bare `except` or `except Exception`.
- Use `async`/`await`; do not mix threads and coroutines. Prefer
  `asyncio.TaskGroup` for concurrency and `contextlib.asynccontextmanager` for
  async resources.
- Use `dataclass` or Pydantic models for data containers and frozen dataclasses
  for immutable data.
- One module has one public class. Name the module after the class in
  `snake_case`; modules holding only related enums or constants are allowed.
  Re-export a package's public API from `__init__.py` with explicit `__all__`.
- Use `pyproject.toml`, pytest, and uv or Poetry; do not introduce `setup.py`.

## Repository structure

```text
backend/     Python uv workspace
  domain/    shared kernel: core/, entities/, schemas/
  source_service/, migrator/  service packages
frontend/    Vite + React SPA
nginx/       static SPA and API proxy
docker-compose.yml, README, .github, .codex
```

- Run uv commands from `backend/`. Its `pyproject.toml` is a virtual workspace
  root; `domain` and each service are workspace members.
- ORM schemas live only in `domain.schemas`. Alembic history is centralized in
  `migrator`, which imports `domain.schemas`.
- Services may depend on `domain` and the message bus, never on another service.
- New services are copied from `backend/source_service`, added to the uv
  workspace and `docker-compose.yml`, and have their own uniquely named
  package and Dockerfile.
- Package names match their directories without a prefix: `source-service` ↔
  `source_service`. The virtual workspace root is the only non-package
  `pyproject.toml`.
- Lint backend code with `uvx ruff@0.14.0 check backend` from the repository
  root. Lint the frontend with `npm run lint` in `frontend/`.
- `frontend/` is a Vite React SPA with no SSR; `npm run build` produces `dist/`.
- Keep CI path-filtered: backend checks `backend/`; frontend checks `frontend/`.
- `docker-compose.yml` is at the root. Only nginx publishes host port 80;
  backend services, Postgres, and RabbitMQ are internal. nginx maps
  `/api/sources/*` to `source_service:8000` and strips `/api/sources`.

## Documentation

- Every non-generated folder has a concise `README.md` with a file map and,
  where useful, local implementation notes.
- Update that README whenever files are added, removed, renamed, or materially
  changed. Exempt generated and ignored directories such as `node_modules`,
  `dist`, `.venv`, `__pycache__`, and caches.

## Logging

- Log every logical action exactly once at the layer that owns it. Log the
  outcome; also log start and result for work that can hang or partially fail.
  Log skips and no-ops with their reason.
- Use `INFO` for business events, `WARNING` for handled degradation, `ERROR`
  for unrecovered failures, and `DEBUG` for per-item or payload noise.
- Use lowercase, stable, greppable messages:
  `<subject> <verb-ed>: key=value key=value`.
- Use `%s` lazy arguments in log calls, never f-strings. Include an `id`,
  `link`, or `url`; never log tokens, passwords, or session strings.
- Cap noisy third-party transport/protocol loggers at `INFO` in
  `domain.core.logging.NOISY_LOGGERS`; do not silence them entirely.

## Git

- Never commit automatically. Do not commit directly to `main`; work on a
  `feat/...` or `fix/...` branch and open a PR.
- Before a commit, run the relevant checks. For backend work, run `ruff` and
  `mypy` (and `pytest -q` when applicable); for frontend work, run its lint and
  relevant tests.
- Use Conventional Commits: `type(scope): subject`. The subject is imperative,
  lowercase, has a space after the colon, and no trailing period.
- Prefer `feat`, `fix`, `chore`, or `refactor`; use `docs`, `test`, `perf`, or
  `style` when more accurate. Include a bulleted body for multiple meaningful
  changes.

## Responses

- Respond in English, directly and concisely. Include only information relevant
  to the task; do not repeat the user's request or add pleasantries.
