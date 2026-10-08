"""Public database integration API for composition and Alembic."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from quont_sandbox.configuration import Settings

from .models import Base
from .postgres import PostgresAssetRepository


def create_database_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)


__all__ = ["Base", "PostgresAssetRepository", "create_database_engine", "create_session_factory"]
