# domain

Pure news-service concepts and rules. The application layer orchestrates them; infrastructure
only persists or evaluates them. One package per entity — the entity module at its root,
`model/` for what it is made of, `rules/` for what judges it (see each package's own README).

- `event_summary/` — `EventSummary`: one news item's event understanding (text, embedding,
  primary-event flag), plus the ingestion-stage values it is built from.
- `event_cluster/` — `EventCluster`: the group of news items both same-event membership and
  relevance ranking act on, plus what judges and forms it. Deduplication and ranking are
  processes that act on this one entity, not entities themselves.
- `company_profile/` — `CompanyProfile`: the monitored company the impact judge is grounded in.
