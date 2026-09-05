# application

Use-case / orchestration layer. Coordinates via **ports** (interfaces it defines and
infrastructure implements); depends on the shared `domain` package (schemas +
entities), never on concrete infra. Collaborators are injected by the composition
root (`deps.py`).

- `ports/` — the interfaces (Protocols): `NpaRepository` (data access).
- `dto/` — the response DTO (Pydantic) for the API.
- `services/` — `NpaCatalog` (list / get / create), one class per module.
- `errors.py` — `NpaAlreadyExistsError` (an act with that `url` is already stored; the
  API maps it to 409).

Notes: import ports (`application.ports`), not infra classes. The create input is the
shared `domain.entities.npa.NpaDTO`, not a local DTO — it is the cross-service contract.
