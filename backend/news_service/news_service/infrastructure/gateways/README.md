# gateways

Outbound adapters to other services' HTTP APIs — the port implementations through
which `news_service` *calls out* (the mirror image of `repositories/`, which talks to
the DB).

- `npa_http_gateway.py` — `HttpNpaGateway`: implements `NpaGateway` over httpx.
  `create` POSTs the `NpaDTO` (JSON, `HttpUrl` serialised as a string) to
  `settings.npa.npa_service_url` + `/` with a 10 s timeout and returns the created act's
  `id`. A **409** becomes `NpaConflictError`; any transport error or other non-2xx
  becomes `NpaGatewayError` — both logged at WARNING here, then left to the use case
  to roll back on.

Notes: a short-lived `httpx.AsyncClient` per call — escalation is a rare human action,
so a pooled client with a lifespan is not worth its wiring. Services still never import
each other: the payload is the shared `common.entities.npa.NpaDTO`, the wire is HTTP.
