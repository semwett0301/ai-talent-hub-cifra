# dto

Cross-service contract — the DTOs and routing shared by the producer
(`source_service`) and any consumer (summarizer, …). This is the single source of
truth for the bus payloads. Put here anything used in the contract between services;
shared enums live next door in `common/enums`.

- `news.py` — `NewsDTO`: what gets published to the `news` exchange
  (`schema_version`, `source_link`, `source_type`, `url`, `text`, `published_at`, `raw`).
  `source_link` is the source's primary key (its URL/channel), not a surrogate id.
- `routing.py` — `routing_key(source_type)` → `news.raw.<type>`; `ROUTING_PREFIX`.

Notes: bump `schema_version` on breaking changes.
