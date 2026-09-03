# dto

Application request/response schemas (Pydantic), grouped by resource. Distinct from
`common.dto`, which is the **bus** contract (`NewsDTO`).

- `source/` — DTOs for the `Source` resource.

Notes: use cases take/return these; the API layer passes them through. Output DTOs
set `from_attributes=True` to build from the ORM `Source`.
