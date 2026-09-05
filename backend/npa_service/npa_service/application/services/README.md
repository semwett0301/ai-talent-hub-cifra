# services

Application services — use cases, one public class per module (re-exported from
`__init__.py`).

- `npa_catalog.py` — `NpaCatalog`: list (paged, newest first), get one (None for an
  unknown id, which the API maps to 404), and create from an `NpaDTO` — logs one
  `npa created` line; lets `NpaAlreadyExistsError` propagate (API → 409).

Notes: collaborators are injected from the root `deps.py` as ports, never concrete
infra.
