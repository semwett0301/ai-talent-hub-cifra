# domain

The innermost layer — business entities and the rules around them. **No
dependencies** (no I/O, no framework, no other layer); every other layer may depend
on it.

- `entities/` — business entities (`NewsItem`), plus their invariants/errors as they
  appear.

Notes: no imports of `application`/`infrastructure`/`api` here. New business concepts
(entities, value objects, domain errors) live under `entities/` or a sibling package.
