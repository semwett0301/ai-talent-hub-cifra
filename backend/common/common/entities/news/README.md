# common.entities.news

The `news` exchange contract, shared by the producer (`source_service`) and any
consumer. Re-exported from `__init__.py` — import `from common.entities.news import …`.

- `dto.py` — everything the domain shares, in one module: `SourceType` (how a post was
  collected), `NewsDTO` (the published payload — also carries the source's `id` and
  `SourceReliability`, imported from `common.entities.source`), and `routing_key` /
  `ROUTING_PREFIX` (`news.raw.<type>`).

Notes: grouped by domain on purpose — `NewsDTO` carries a `SourceType` and a
`SourceReliability`, and both travel with the routing key, so a consumer never has to
call back into `source_service` for source metadata. `source_id` is optional on the wire:
the consumer nulls it when the source was deleted before the batch was stored, so a
message never fails on a dangling id. `NewsDTO.schema_version` guards the wire format;
bump it on any breaking change (v4 = `source_id`). Deps: pydantic + stdlib only.
