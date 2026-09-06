# ports

The interfaces application depends on and infrastructure implements (`Protocol`).
Impls **inherit** the port (explicit conformance). Re-exported from `__init__.py`.

- `repositories.py` — current/tracked reads, immutable versions, registration, atomic
  transitions, and unchanged-check metadata.
- `npa_source.py` — authoritative State Duma snapshot input.
- `change_summarizer.py` — plain-language comparison of two texts.

Notes: port implementations are injected in `deps.py`; application services never import
HTTP, DOCX, OpenRouter, APScheduler, or SQLAlchemy session mechanics.
