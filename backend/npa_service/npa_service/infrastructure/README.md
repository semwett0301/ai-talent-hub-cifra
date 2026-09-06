# infrastructure

Implementations of the application ports plus adapters to the outside world.
Depends on `application` (the ports) and `common`; nothing depends inward on it except
the composition root (`deps.py`).

- `repositories/` — `NpaRepo` over the ORM, a session per call (the `Npa` table itself
  lives in `common/schemas/`).
- `duma/` — allow-listed HTTP collection plus bill-page and DOCX parsing.
- `llm/` — structured OpenRouter/DeepSeek change summaries.
- `scheduling/` — one coalesced daily APScheduler job.
- `simulation/` — opt-in deterministic local-only Duma/LLM replacements for the browser demo.

Notes: classes here implement the ports (they inherit the `Protocol`); `deps.py`
constructs them and injects them where a port is expected. DB engine/session come
from `common.core.db`.
