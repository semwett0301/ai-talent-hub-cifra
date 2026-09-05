# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). Re-exported from `__init__.py`.

- `repositories.py` — `NpaRepository`: `list_all(limit, offset)` (newest first),
  `get(id)` (None when unknown), `add(NpaDTO)` (inserts and returns the row; raises
  `NpaAlreadyExistsError` when the `url` is already stored).

Notes: ports reference `domain.schemas.Npa` and the shared `domain.entities.npa.NpaDTO`
contract directly.
