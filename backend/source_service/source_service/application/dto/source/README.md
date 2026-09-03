# source

DTOs for the `Source` resource — one class per module, re-exported from `__init__.py`
(import as `from source_service.application.dto.source import SourceCreate`).

- `create.py` — `SourceCreate`: fields accepted when creating a source.
- `update.py` — `SourceUpdate`: all-optional fields for a partial update (PATCH).
- `out.py` — `SourceOut`: the response shape (`from_attributes=True`, built from ORM).

Notes: the module name drops the redundant `source` prefix (enclosing package already
names it) — `create.py`, not `source_create.py`.
