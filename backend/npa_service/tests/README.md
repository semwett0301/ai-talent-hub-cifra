# tests

- `test_duma_parsing.py` — strict URL allow-list, representative Duma stage/document
  parsing, and in-memory DOCX extraction.
- `test_npa_state.py` — initial/terminal State transitions, changed-version persistence,
  publication stopping, unchanged-state model-call avoidance, and the local simulation
  sequence using fakes only.

Tests never call the State Duma site or OpenRouter.
