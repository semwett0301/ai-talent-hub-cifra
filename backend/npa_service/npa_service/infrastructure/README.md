# infrastructure

Implementations of the application ports plus adapters to the outside world (DB).
Depends on `application` (the ports) and `domain`; nothing depends inward on it except
the composition root (`deps.py`).

- `repositories/` — `NpaRepo` over the ORM, a session per call (the `Npa` table itself
  lives in `domain/schemas/`).

Notes: classes here implement the ports (they inherit the `Protocol`); `deps.py`
constructs them and injects them where a port is expected. DB engine/session come
from `domain.core.db`.
