from datetime import date

import pytest

from quont_sandbox.assets import Asset, ExternalIdentifier, Instrument, Venue
from quont_sandbox.assets.infrastructure.memory import InMemoryAssetRepository
from quont_sandbox.common import AssetClass, ValidationError


def test_open_identifier_interval_can_close_without_rewriting_history() -> None:
    repository = InMemoryAssetRepository()
    asset = Asset(name="Synthetic", asset_class=AssetClass.EQUITY)
    venue = Venue(code="XTEST", name="Test")
    instrument = Instrument(asset_id=asset.asset_id, venue_id=venue.venue_id)
    repository.save_asset(asset)
    repository.save_venue(venue)
    repository.save_instrument(instrument)
    other_instrument = Instrument(asset_id=asset.asset_id, venue_id=venue.venue_id)
    repository.save_instrument(other_instrument)
    original = ExternalIdentifier(
        instrument_id=instrument.instrument_id,
        namespace="ticker",
        value="OLD",
        valid_from=date(2020, 1, 1),
    )
    repository.save_identifier(original)
    closed = ExternalIdentifier.model_validate(
        original.model_dump() | {"valid_to": date(2021, 1, 1)}
    )
    repository.save_identifier(closed)
    repository.save_identifier(closed)
    replacement = ExternalIdentifier(
        instrument_id=instrument.instrument_id,
        namespace="ticker",
        value="NEW",
        valid_from=date(2021, 1, 1),
    )
    repository.save_identifier(replacement)
    assert repository.list_identifiers(instrument.instrument_id) == (closed, replacement)
    for change in (
        {"valid_to": None},
        {"valid_to": date(2022, 1, 1)},
        {"value": "REWRITE"},
        {"instrument_id": other_instrument.instrument_id},
    ):
        revised = ExternalIdentifier.model_validate(closed.model_dump() | change)
        with pytest.raises(ValidationError, match="immutable"):
            repository.save_identifier(revised)
