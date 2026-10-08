"""Alembic uses the same configuration precedence as the application."""

import os
from pathlib import Path

from alembic import context
from sqlalchemy import Connection

from quont_sandbox.assets.infrastructure.database import Base, create_database_engine
from quont_sandbox.configuration import load_settings


def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def main() -> None:
    # Programmatic callers may supply a connection to keep schema-scoped tests isolated.
    connection = context.config.attributes.get("connection")
    if isinstance(connection, Connection):
        run_migrations(connection)
        return
    config_path = os.environ.get("QUONT_CONFIG_FILE")
    settings = load_settings(Path(config_path) if config_path else None)
    if context.is_offline_mode():
        context.configure(
            url=settings.database_url.get_secret_value(),
            target_metadata=Base.metadata,
            literal_binds=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    else:
        engine = create_database_engine(settings)
        try:
            with engine.connect() as connection:
                run_migrations(connection)
        finally:
            engine.dispose()


main()
