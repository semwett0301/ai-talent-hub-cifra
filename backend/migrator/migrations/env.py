"""Alembic environment — the shared DB schema history (sync engine, psycopg2).

Owns migrations for every service on the one database. All ORM models live in the
shared `domain.schemas` package; importing it registers every table on
`Base.metadata` for both `upgrade` and `--autogenerate`.
"""

from logging.config import fileConfig

import domain.schemas  # noqa: F401 — import registers every ORM model on Base.metadata
from alembic import context
from domain.core.base import Base
from domain.core.settings import settings
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.sync_database_url)

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
