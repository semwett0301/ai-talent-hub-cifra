# entities

Business entities — the core domain objects, re-exported from `__init__.py`.

- `news_item.py` — `NewsItem`: the normalized unit every collector emits (url, text,
  published_at, raw).

Notes: pure Python, no framework/ORM/I/O. Import as `from source_service.domain.entities
import NewsItem`.
