# dto

Application response schemas (Pydantic), grouped by resource. Distinct from
`common.entities.npa`, which is the **cross-service** contract (`NpaDTO`).

- `npa/` — DTOs for the `Npa` resource.

Notes: the API builds these from application results. Output DTOs set
`from_attributes=True` to build from persisted current/version rows.
