# ports/gateways

Mirrors `infrastructure/gateways/` — one port per implementation there.

- `npa_gateway.py` — `NpaGateway`: `create(NpaDTO) -> id` registers an act in
  `npa_service`; raises `NpaConflictError` (409 there) or `NpaGatewayError` (anything
  else) instead of returning a sentinel, so the use case can stop before `commit()`.
