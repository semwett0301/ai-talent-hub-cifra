# entities

Plain domain shapes with no DB involvement, one public class per module
(re-exported from `__init__.py`).

- `news_item.py` — `NewsItem`: `@dataclass` collectors emit; never stored.

Notes: no dependencies beyond the stdlib. Contrast with `../schemas/`, which
holds DB-backed shapes.
