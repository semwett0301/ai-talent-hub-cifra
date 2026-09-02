# common

Shared library imported as `common` by every service.

- `core/` — config and logging.
- (later) `db/`, `models/`, `schemas/`, `llm/` as the app needs them.

Notes: the one place for cross-service code — don't duplicate into services.
Models, when added, live only here (`common.models`).
