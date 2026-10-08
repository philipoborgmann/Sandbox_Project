"""SQLAlchemy catalogue adapter; the caller owns commit/rollback boundaries."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from quont_sandbox.common import AssetClass, DataNotFoundError

from ..domain import Asset, ExternalIdentifier, Instrument, Venue, validate_identifier_update
from .models import AssetRow, ExternalIdentifierRow, InstrumentRow, VenueRow


def asset_from_row(row: AssetRow) -> Asset:
    return Asset(asset_id=row.asset_id, name=row.name, asset_class=AssetClass(row.asset_class))


def identifier_from_row(row: ExternalIdentifierRow) -> ExternalIdentifier:
    return ExternalIdentifier(
        identifier_id=row.identifier_id,
        instrument_id=row.instrument_id,
        namespace=row.namespace,
        value=row.value,
        valid_from=row.valid_from,
        valid_to=row.valid_to,
    )


class PostgresAssetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_asset(self, asset: Asset) -> None:
        self.session.merge(
            AssetRow(asset_id=asset.asset_id, name=asset.name, asset_class=asset.asset_class.value)
        )
        self.session.flush()

    def get_asset(self, asset_id: UUID) -> Asset:
        row = self.session.get(AssetRow, asset_id)
        if row is None:
            raise DataNotFoundError("Asset not found")
        return asset_from_row(row)

    def list_assets(self) -> tuple[Asset, ...]:
        return tuple(
            asset_from_row(row)
            for row in self.session.scalars(select(AssetRow).order_by(AssetRow.asset_id))
        )

    def save_venue(self, venue: Venue) -> None:
        self.session.merge(VenueRow(venue_id=venue.venue_id, code=venue.code, name=venue.name))
        self.session.flush()

    def get_venue(self, venue_id: UUID) -> Venue:
        row = self.session.get(VenueRow, venue_id)
        if row is None:
            raise DataNotFoundError("Venue not found")
        return Venue(venue_id=row.venue_id, code=row.code, name=row.name)

    def save_instrument(self, instrument: Instrument) -> None:
        self.get_asset(instrument.asset_id)
        self.get_venue(instrument.venue_id)
        self.session.merge(
            InstrumentRow(
                instrument_id=instrument.instrument_id,
                asset_id=instrument.asset_id,
                venue_id=instrument.venue_id,
            )
        )
        self.session.flush()

    def get_instrument(self, instrument_id: UUID) -> Instrument:
        row = self.session.get(InstrumentRow, instrument_id)
        if row is None:
            raise DataNotFoundError("Instrument not found")
        return Instrument(
            instrument_id=row.instrument_id, asset_id=row.asset_id, venue_id=row.venue_id
        )

    def list_instruments(self, asset_id: UUID) -> tuple[Instrument, ...]:
        rows = self.session.scalars(
            select(InstrumentRow)
            .where(InstrumentRow.asset_id == asset_id)
            .order_by(InstrumentRow.instrument_id)
        )
        return tuple(
            Instrument(
                instrument_id=row.instrument_id, asset_id=row.asset_id, venue_id=row.venue_id
            )
            for row in rows
        )

    def save_identifier(self, identifier: ExternalIdentifier) -> None:
        self.get_instrument(identifier.instrument_id)
        row = self.session.get(ExternalIdentifierRow, identifier.identifier_id)
        if row is not None:
            validate_identifier_update(identifier_from_row(row), identifier)
            row.valid_to = identifier.valid_to
            self.session.flush()
            return
        self.session.add(
            ExternalIdentifierRow(
                identifier_id=identifier.identifier_id,
                instrument_id=identifier.instrument_id,
                namespace=identifier.namespace,
                value=identifier.value,
                valid_from=identifier.valid_from,
                valid_to=identifier.valid_to,
            )
        )
        self.session.flush()

    def list_identifiers(self, instrument_id: UUID) -> tuple[ExternalIdentifier, ...]:
        rows = self.session.scalars(
            select(ExternalIdentifierRow)
            .where(ExternalIdentifierRow.instrument_id == instrument_id)
            .order_by(ExternalIdentifierRow.valid_from, ExternalIdentifierRow.identifier_id)
        )
        return tuple(identifier_from_row(row) for row in rows)
