"""Alembic environment — the shared DB schema history (sync engine, psycopg2).

Owns migrations for every service on the one database. Service models are
imported lazily (only for `--autogenerate`) via `migrations.autogenerate`, so the
one-shot `upgrade` image stays free of every service package.
"""

from logging.config import fileConfig

from alembic import context
from common.core.base import Base
from common.settings import settings
from migrations.autogenerate import is_autogenerate, load_service_models
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.sync_database_url)

if is_autogenerate(config):
    load_service_models()
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.sync_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
