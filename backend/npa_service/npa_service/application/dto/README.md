# dto

Application response schemas (Pydantic), grouped by resource. Distinct from
`domain.entities.npa`, which is the **cross-service** contract (`NpaDTO`).

- `npa/` — DTOs for the `Npa` resource.

Notes: use cases return these; the API layer passes them through. Output DTOs set
`from_attributes=True` to build from the ORM `Npa`.
