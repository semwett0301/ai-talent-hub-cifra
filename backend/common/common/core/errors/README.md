# common.core.errors

Domain-wide error types — the signals shared between a service's application layer and
the shared mechanisms in `core` (bus consumer, loaders). One class per module,
re-exported from `__init__.py`; import from the package (`from common.core.errors import
BatchStoreError`).

- `batch_store.py` — `BatchStoreError`: a batch could not be persisted as a whole. Raised
  by the code that writes a batch; caught by whatever fed it, which decides the items'
  fate (the RabbitMQ consumer nacks them — requeue or drop per its config). Services
  subclass it (`NewsStoreError`) so shared code catches them without knowing the service.

Notes: keep these transport-agnostic — nothing here may import `rabbit`, `db`, or a
service. Anything specific to one transport belongs in that subpackage.
