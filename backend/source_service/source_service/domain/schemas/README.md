# schemas

The service's data shapes, one public class per module (re-exported from
`__init__.py`). DB-backed and in-memory shapes live together — they differ only in
whether they touch the DB.

- `source.py` — `Source`: SQLAlchemy ORM model for the `source` table (the table this
  service owns; its schema history lives in `../../../migrator`).
- `news_item.py` — `NewsItem`: plain `@dataclass` collectors emit; never stored.

Notes: `Source` imports `common.core.base.Base` and SQLAlchemy; `NewsItem` has no
dependencies. The migrator imports this package (`source_service.domain.schemas`) to
pick up `Source` for autogenerate.
