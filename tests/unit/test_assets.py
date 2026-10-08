from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError as PydanticValidationError

from quont_sandbox.assets import Asset, AssetRepository, ExternalIdentifier, Instrument, Venue
from quont_sandbox.assets.infrastructure.memory import InMemoryAssetRepository
from quont_sandbox.common import (
    AssetClass,
    ConfigurationError,
    DataError,
    DataNotFoundError,
    Frequency,
    ProviderError,
    QuontSandboxError,
    ValidationError,
)


def test_controlled_values_and_exceptions() -> None:
    assert {value.value for value in AssetClass} == {"EQUITY", "ETF", "CRYPTO"}
    assert [value.value for value in Frequency] == ["1m", "5m", "1h", "1d", "1mo"]
    assert issubclass(ConfigurationError, QuontSandboxError)
    assert issubclass(DataError, QuontSandboxError)
    for exception in (ProviderError, ValidationError, DataNotFoundError):
        assert issubclass(exception, DataError)


def test_stable_identity_and_multiple_listings() -> None:
    repository: AssetRepository = InMemoryAssetRepository()
    asset = Asset(name="Example", asset_class=AssetClass.EQUITY)
    other = Asset(name="Example", asset_class=AssetClass.EQUITY)
    assert asset.asset_id != other.asset_id
    repository.save_asset(asset)
    first = Venue(code="XONE", name="First market")
    second = Venue(code="XTWO", name="Second market")
    for venue in (first, second):
        repository.save_venue(venue)
        repository.save_instrument(Instrument(asset_id=asset.asset_id, venue_id=venue.venue_id))
    instruments = repository.list_instruments(asset.asset_id)
    assert len(instruments) == 2
    assert {row.venue_id for row in instruments} == {first.venue_id, second.venue_id}
    instrument = instruments[0]
    old = ExternalIdentifier(
        instrument_id=instrument.instrument_id,
        namespace="ticker",
        value="OLD",
        valid_from=date(2020, 1, 1),
        valid_to=date(2021, 1, 1),
    )
    new = ExternalIdentifier(
        instrument_id=instrument.instrument_id,
        namespace="ticker",
        value="NEW",
        valid_from=date(2021, 1, 1),
    )
    repository.save_identifier(old)
    repository.save_identifier(new)
    assert repository.list_identifiers(instrument.instrument_id) == (old, new)
    renamed = Asset(asset_id=asset.asset_id, name="Renamed", asset_class=asset.asset_class)
    repository.save_asset(renamed)
    assert repository.get_asset(asset.asset_id) == renamed
    assert repository.get_instrument(instrument.instrument_id) == instrument
    assert repository.get_venue(first.venue_id) == first
    assert repository.list_assets() == (renamed,)
    with pytest.raises(ValidationError, match="immutable"):
        repository.save_identifier(
            ExternalIdentifier(
                identifier_id=old.identifier_id,
                instrument_id=instrument.instrument_id,
                namespace="ticker",
                value="REWRITE",
                valid_from=old.valid_from,
            )
        )


def test_catalogue_constraints() -> None:
    repository = InMemoryAssetRepository()
    with pytest.raises(DataNotFoundError):
        repository.get_asset(uuid4())
    with pytest.raises(DataNotFoundError):
        repository.get_venue(uuid4())
    with pytest.raises(DataNotFoundError):
        repository.get_instrument(uuid4())
    with pytest.raises(DataNotFoundError):
        repository.save_instrument(Instrument(asset_id=uuid4(), venue_id=uuid4()))
    venue = Venue(code="XONE", name="First")
    repository.save_venue(venue)
    with pytest.raises(ValidationError):
        repository.save_venue(Venue(code="XONE", name="Duplicate"))
    with pytest.raises(PydanticValidationError):
        ExternalIdentifier(
            instrument_id=uuid4(),
            namespace="ticker",
            value="BAD",
            valid_from=date(2021, 1, 1),
            valid_to=date(2020, 1, 1),
        )
