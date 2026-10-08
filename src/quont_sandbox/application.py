"""Composition of the initial catalogue and local storage use cases."""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from .assets import Asset, list_assets
from .assets.infrastructure.database import (
    PostgresAssetRepository,
    create_database_engine,
    create_session_factory,
)
from .common import DataError
from .configuration import Settings


@dataclass(frozen=True)
class StorageDirectories:
    raw: Path
    cache: Path
    exports: Path


def storage_directories(settings: Settings) -> StorageDirectories:
    return StorageDirectories(
        settings.raw_dir.resolve(), settings.cache_dir.resolve(), settings.exports_dir.resolve()
    )


def read_asset_catalogue(settings: Settings) -> tuple[Asset, ...]:
    engine = create_database_engine(settings)
    try:
        with create_session_factory(engine)() as session:
            return list_assets(PostgresAssetRepository(session))
    except SQLAlchemyError as error:
        raise DataError(
            "Cannot read asset catalogue; check database configuration and migrations"
        ) from error
    finally:
        engine.dispose()
