# common.entities.news

The `news` exchange contract, shared by the producer (`source_service`) and any
consumer. Re-exported from `__init__.py` — import `from common.entities.news import …`.

- `dto.py` — everything the domain shares, in one module: `SourceType` (how a post was
  collected), `NewsDTO` (the published payload, one flat typed record: the source's
  `id` / `link` / `name` / `type` / `SourceReliability` / `source_tags`, then `url`,
  `title`, `text`, `excerpt`, `published_at`, `updated_at`), its
  `for_source(source, …)` factory, and `routing_key` / `ROUTING_PREFIX`
  (`news.raw.<type>`).

Notes: grouped by domain on purpose — `NewsDTO` carries everything a consumer shows
about the source, so it never calls back into `source_service`. **No `raw` blob**: what a
source type cannot supply stays `None` (a Telegram post has no `excerpt`),
`title` is always set (the Telegram collector uses the post's first sentence), and
crawler provenance lives in `source_service` logs, not on the wire. `source_id` is
required — a news item always has its source; the consumer skips items whose source
vanished mid-flight. `for_source` takes the `Source` row under `TYPE_CHECKING` only
(`common.schemas` imports this module, a runtime import back would cycle).
`NewsDTO.schema_version` (`SCHEMA_VERSION`) guards the wire format; bump it on any
breaking change (v5 = flat shape, no `raw`). Deps: pydantic + stdlib only.
