# domain.entities.source

The `Source` resource's own shapes — separate from `entities/news`'s message-contract
shapes, even though `SourceReliability` also rides along inside `NewsDTO` (see below).

- `dto.py` — `SourceReliability`: how trustworthy a source's reporting is (`high` /
  `medium` / `low`), curated per source.

Notes: kept in its own subpackage rather than folded into `entities/news` because
`SourceReliability` is fundamentally a `Source` attribute (set on the resource, not
computed per-message like `SourceType`); `entities/news` imports it from here and embeds
it in `NewsDTO` so a `news` consumer never has to call back into `source_service`. Deps:
stdlib only.
