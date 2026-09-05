# source

DTOs for the `Source` resource — one class per module, re-exported from `__init__.py`
(import as `from source_service.application.dto.source import SourceCreate`).

- `create.py` — `SourceCreate`: fields accepted when creating a source, including
  `reliability` (`common.entities.source.SourceReliability`, defaults to
  `MEDIUM`). **No `type`** — `SourceService` auto-detects it from `link` (see
  `application/parse/`).
- `update.py` — `SourceUpdate`: all-optional fields for a partial update (PATCH),
  including `reliability`; also has no `type` — changing `link` re-triggers
  detection instead.
- `out.py` — `SourceOut`: the response shape (`from_attributes=True`, built from
  ORM); `type` is read-only, server-computed; `reliability` is client-set.

Notes: the module name drops the redundant `source` prefix (enclosing package already
names it) — `create.py`, not `source_create.py`.
