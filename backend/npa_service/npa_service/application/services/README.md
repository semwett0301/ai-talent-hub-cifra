# services

Application services — use cases, one public class per module (re-exported from
`__init__.py`).

- `npa_catalog.py` — paged list, get one, and immutable version history reads.
- `npa_registration.py` — fetches and validates a Duma URL, parses its current Word
  text, enters the State pattern, and persists the initial snapshot.
- `npa_monitor.py` — daily transition orchestration. Unchanged acts only update their
  check metadata; stage/document changes are summarized and versioned; publication
  transitions to the terminal state.

Notes: collaborators are injected from the root `deps.py` as ports, never concrete
infra.
