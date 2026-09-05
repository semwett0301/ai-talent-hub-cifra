# entities.npa

The `npa` domain (нормативно-правовой акт — a legislative act).

- `dto.py` — `NpaDTO`: the act as it crosses service boundaries — `url` (`HttpUrl`, the
  act's identity, unique in the store), `title`, `text`, optional `published_at`.
  `news_service` posts it to `npa_service`; `npa_service` accepts it on `POST /`.

Notes: this is the HTTP contract between the two services (the way `entities/news` is
the bus contract) — change it here, both sides follow. No `id`: the store generates it.
