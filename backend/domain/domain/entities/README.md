# domain.entities

Shared **business entities**, **organized by domain** like a domain layer — not by
technical kind (no `dto/` + `enums/` split). Each domain gets its own subpackage
holding everything about that concept.

- `news/` — the `news` domain: `NewsDTO` (the item shape published to the `news`
  exchange), its `SourceType`, and the routing key — grouped together (a news item
  always has a source), all in `dto.py`.
- `source/` — the `Source` resource's own shapes, e.g. `SourceReliability`.
- `npa/` — the `npa` domain (legislative acts): `NpaDTO`, the HTTP contract
  `news_service` posts to `npa_service` and `npa_service` accepts on create.

Notes: keep these dependency-light (pydantic + stdlib) so any service can depend on an
entity without pulling DB/LLM infra. Add a sibling subpackage per new domain. `news`
depends on `source` (`NewsDTO` embeds `SourceReliability`) — never the other way.
