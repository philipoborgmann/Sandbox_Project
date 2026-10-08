"""Opt-in real PostgreSQL tests; isolated schema, no SQLite substitute."""

import os
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Connection, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from quont_sandbox.assets import Asset, ExternalIdentifier, Instrument, Venue
from quont_sandbox.assets.infrastructure.database import Base, create_database_engine
from quont_sandbox.assets.infrastructure.models import (
    ExternalIdentifierRow,
    InstrumentRow,
    VenueRow,
)
from quont_sandbox.assets.infrastructure.postgres import PostgresAssetRepository
from quont_sandbox.common import AssetClass, ValidationError
from quont_sandbox.configuration import load_settings

pytestmark = pytest.mark.database
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def migrated_connection() -> Iterator[Connection]:
    url = os.environ.get("QUONT_TEST_DATABASE_URL")
    if not url:
        pytest.skip("QUONT_TEST_DATABASE_URL is not configured")
    settings = load_settings(environ={}, overrides={"database_url": url})
    engine = create_database_engine(settings)
    schema = "quont_test_" + uuid4().hex
    try:
        with engine.connect() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET search_path TO "{schema}"'))
            connection.commit()
            try:
                config = Config(str(ROOT / "alembic.ini"))
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
                yield connection
                connection.rollback()
                command.downgrade(config, "base")
                assert set(inspect(connection).get_table_names()) == {"alembic_version"}
            finally:
                connection.rollback()
                connection.execute(text("SET search_path TO public"))
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
                connection.commit()
    finally:
        engine.dispose()


def test_migration_round_trip_and_constraints(migrated_connection: Connection) -> None:
    connection = migrated_connection
    migration_context = MigrationContext.configure(connection)
    assert compare_metadata(migration_context, Base.metadata) == []
    asset = Asset(name="Synthetic equity", asset_class=AssetClass.EQUITY)
    venue = Venue(code="XTEST", name="Test market")
    instrument = Instrument(asset_id=asset.asset_id, venue_id=venue.venue_id)
    identifier = ExternalIdentifier(
        instrument_id=instrument.instrument_id,
        namespace="ticker",
        value="TEST",
        valid_from=date(2024, 1, 1),
    )
    with Session(connection) as session:
        repository = PostgresAssetRepository(session)
        repository.save_asset(asset)
        repository.save_venue(venue)
        repository.save_instrument(instrument)
        repository.save_identifier(identifier)
        session.commit()
    with Session(connection) as session:
        repository = PostgresAssetRepository(session)
        assert repository.get_asset(asset.asset_id) == asset
        assert repository.get_venue(venue.venue_id) == venue
        assert repository.get_instrument(instrument.instrument_id) == instrument
        assert repository.list_assets() == (asset,)
        assert repository.list_instruments(asset.asset_id) == (instrument,)
        assert repository.list_identifiers(instrument.instrument_id) == (identifier,)
        with pytest.raises(ValidationError):
            repository.save_identifier(
                ExternalIdentifier(
                    identifier_id=identifier.identifier_id,
                    instrument_id=instrument.instrument_id,
                    namespace="ticker",
                    value="REWRITE",
                    valid_from=identifier.valid_from,
                )
            )
        closed = ExternalIdentifier.model_validate(
            identifier.model_dump() | {"valid_to": date(2025, 1, 1)}
        )
        repository.save_identifier(closed)
        session.commit()
    with Session(connection) as session:
        repository = PostgresAssetRepository(session)
        assert repository.list_identifiers(instrument.instrument_id) == (closed,)
        with pytest.raises(ValidationError):
            repository.save_identifier(identifier)
    with Session(connection) as session, pytest.raises(IntegrityError):
        session.add(VenueRow(venue_id=uuid4(), code=venue.code, name="Duplicate"))
        session.flush()
    with Session(connection) as session, pytest.raises(IntegrityError):
        session.add(InstrumentRow(instrument_id=uuid4(), asset_id=uuid4(), venue_id=venue.venue_id))
        session.flush()
    with Session(connection) as session, pytest.raises(IntegrityError):
        session.add(
            ExternalIdentifierRow(
                identifier_id=uuid4(),
                instrument_id=instrument.instrument_id,
                namespace="ticker",
                value="BAD",
                valid_from=date(2024, 1, 2),
                valid_to=date(2024, 1, 1),
            )
        )
        session.flush()
