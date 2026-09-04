"""Lazy service-model loading for Alembic autogenerate.

Model metadata is only needed to **autogenerate** revisions (to diff
`Base.metadata` against the live DB); `upgrade` just replays the version scripts
and never reads it. So service models are imported only when Alembic runs with
`--autogenerate`, keeping the one-shot `upgrade` image free of every service
package.
"""

from importlib import import_module

from alembic.config import Config

# Every service that owns tables on the shared DB, as its models module. Imported
# only for autogenerate (see load_service_models). Each service ships a uniquely
# named top-level package, so all can coexist — append the next service's models
# module here once it lands.
SERVICE_MODEL_MODULES: tuple[str, ...] = ("source_service.domain.schemas",)


def is_autogenerate(config: Config) -> bool:
    """True when invoked as `alembic revision --autogenerate`."""
    cmd_opts = getattr(config, "cmd_opts", None)
    return bool(getattr(cmd_opts, "autogenerate", False))


def load_service_models() -> None:
    """Import each service's models so Base.metadata is complete for autogenerate."""
    for module_name in SERVICE_MODEL_MODULES:
        import_module(module_name)
