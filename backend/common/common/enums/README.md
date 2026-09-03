# enums

Shared enums — reused by the DTO contract (`common/dto`) and by services. A
sibling of `dto/`: enums are the vocabulary the contract and the models agree on,
kept separate from the payload shapes themselves.

- `source.py` — `SourceType` (`telegram` / `rss` / `web`): how a source is collected.

Notes: re-exported from `__init__.py`, so import as `from common.enums import SourceType`.
Add an enum here only once ≥2 places share it; single-service enums stay in the service.
