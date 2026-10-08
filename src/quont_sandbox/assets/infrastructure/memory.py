"""In-memory catalogue with foreign-key and uniqueness semantics."""

from uuid import UUID

from quont_sandbox.common import DataNotFoundError, ValidationError

from ..domain import Asset, ExternalIdentifier, Instrument, Venue, validate_identifier_update


class InMemoryAssetRepository:
    def __init__(self) -> None:
        self._assets: dict[UUID, Asset] = {}
        self._venues: dict[UUID, Venue] = {}
        self._instruments: dict[UUID, Instrument] = {}
        self._identifiers: dict[UUID, ExternalIdentifier] = {}

    def save_asset(self, asset: Asset) -> None:
        self._assets[asset.asset_id] = asset

    def get_asset(self, asset_id: UUID) -> Asset:
        try:
            return self._assets[asset_id]
        except KeyError as error:
            raise DataNotFoundError("Asset not found") from error

    def list_assets(self) -> tuple[Asset, ...]:
        return tuple(self._assets.values())

    def save_venue(self, venue: Venue) -> None:
        if any(
            row.code == venue.code and row.venue_id != venue.venue_id
            for row in self._venues.values()
        ):
            raise ValidationError("Venue code already exists")
        self._venues[venue.venue_id] = venue

    def get_venue(self, venue_id: UUID) -> Venue:
        try:
            return self._venues[venue_id]
        except KeyError as error:
            raise DataNotFoundError("Venue not found") from error

    def save_instrument(self, instrument: Instrument) -> None:
        self.get_asset(instrument.asset_id)
        self.get_venue(instrument.venue_id)
        self._instruments[instrument.instrument_id] = instrument

    def get_instrument(self, instrument_id: UUID) -> Instrument:
        try:
            return self._instruments[instrument_id]
        except KeyError as error:
            raise DataNotFoundError("Instrument not found") from error

    def list_instruments(self, asset_id: UUID) -> tuple[Instrument, ...]:
        return tuple(row for row in self._instruments.values() if row.asset_id == asset_id)

    def save_identifier(self, identifier: ExternalIdentifier) -> None:
        self.get_instrument(identifier.instrument_id)
        existing = self._identifiers.get(identifier.identifier_id)
        if existing is not None:
            validate_identifier_update(existing, identifier)
        if any(
            row.identifier_id != identifier.identifier_id
            and (row.instrument_id, row.namespace, row.value, row.valid_from)
            == (
                identifier.instrument_id,
                identifier.namespace,
                identifier.value,
                identifier.valid_from,
            )
            for row in self._identifiers.values()
        ):
            raise ValidationError("Identifier interval already exists")
        self._identifiers[identifier.identifier_id] = identifier

    def list_identifiers(self, instrument_id: UUID) -> tuple[ExternalIdentifier, ...]:
        return tuple(
            row for row in self._identifiers.values() if row.instrument_id == instrument_id
        )
