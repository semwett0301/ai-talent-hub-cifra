# npa

DTOs for the `Npa` resource — one class per module, re-exported from `__init__.py`
(import as `from npa_service.application.dto.npa import NpaOut`).

- `create.py` — URL-only registration request.
- `out.py` — current stage, tracking status, timestamps, and latest summaries.
- `detail_out.py` / `version_out.py` — detail response with immutable history metadata.
- `article_change_out.py` — changed article with summary and short before/after evidence.

Metadata and text are never accepted from the browser: registration reloads them from the
authoritative Duma page and Word document.
