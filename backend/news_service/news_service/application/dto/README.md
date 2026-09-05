# dto

Application request/response schemas (Pydantic), grouped by resource. Distinct from
`common.entities.news`, which is the **bus** contract (`NewsDTO`).

- `news/` — DTOs for the `News` resource.

Notes: use cases return these; the API layer passes them through. Output DTOs set
`from_attributes=True` to build from the ORM `News`.
