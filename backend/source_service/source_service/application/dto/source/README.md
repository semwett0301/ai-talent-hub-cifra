# source

DTOs for the `Source` resource — one class per module, re-exported from `__init__.py`
(import as `from source_service.application.dto.source import SourceCreate`).

- `link.py` — `SourceLink`: the annotated `str` both input DTOs use, rejecting anything
  that is neither an http(s) URL nor a Telegram link (a 422 straight from Pydantic).
- `create.py` — `SourceCreate`: fields accepted when creating a source. **No
  `poll_interval_seconds`** — the schedule follows from the detected type, so the
  server assigns it. Includes
  `reliability` (`common.entities.source.SourceReliability`, defaults to
  `MEDIUM`). **No `type`** — `SourceService` auto-detects it from `link` (see
  `application/parse/`).
- `update.py` — `SourceUpdate`: all-optional fields for a partial update (PATCH),
  including `reliability` and `poll_interval_seconds` (the list row's frequency
  select is the only place a client sets an interval); no `type` (changing `link` re-triggers detection) and no
  `is_relevant` — that flag isn't client-settable. `is_enabled=true` on a source the
  backend already marked `is_relevant=false` is rejected by `SourceService.update`.
- `out.py` — `SourceOut`: the response shape (`from_attributes=True`, built from
  ORM); `type` and `is_relevant` are read-only, server-computed; `reliability` is
  client-set.

Notes: the module name drops the redundant `source` prefix (enclosing package already
names it) — `create.py`, not `source_create.py`.
