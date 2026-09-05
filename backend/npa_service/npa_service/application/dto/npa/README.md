# npa

DTOs for the `Npa` resource — one class per module, re-exported from `__init__.py`
(import as `from npa_service.application.dto.npa import NpaOut`).

- `out.py` — `NpaOut`: the response shape (`from_attributes=True`, built from ORM) —
  the `NpaDTO` fields plus `id` and `created_at`.

No input DTO: `POST /` takes the shared `common.entities.npa.NpaDTO` directly, so the
service and `news_service` speak one contract.
