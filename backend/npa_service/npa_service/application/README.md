# application

Use-case / orchestration layer. Coordinates via **ports** (interfaces it defines and
infrastructure implements); depends on the shared `common` package (schemas +
entities), never on concrete infra. Collaborators are injected by the composition
root (`deps.py`).

- `ports/` — repository, Duma source, and change-summarizer interfaces.
- `dto/` — the response DTO (Pydantic) for the API.
- `services/` — catalog reads, URL registration, and daily monitoring orchestration.
- `errors/` — typed duplicate, validation, transport, document, and model failures.

Notes: import ports (`application.ports`), not infrastructure classes. Registration uses
the local URL-only DTO; legacy cross-service candidate fields are deliberately ignored.
