# entities.npa

The `npa` domain (нормативно-правовой акт — a legislative act).

- `dto.py` — `NpaDTO`: the act as it crosses service boundaries — `url` (`HttpUrl`, the
  act's identity, unique in the store), `title`, `text`, optional `published_at`.
  `news_service` posts it to `npa_service`, which trusts only the URL and reloads the
  authoritative State Duma metadata and text.
- `status.py` — `NpaTrackingStatus`: tracking continues, has stopped after official
  publication, or is unsupported legacy data.

Notes: the public NPA registration request itself is URL-only. Pydantic ignores the
additional candidate fields sent by the legacy cross-service DTO.
