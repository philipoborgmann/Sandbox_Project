"""Initial asset-only relational schema; domain objects never inherit these rows."""

from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AssetRow(Base):
    __tablename__ = "assets"
    __table_args__ = (
        CheckConstraint("asset_class IN ('EQUITY', 'ETF', 'CRYPTO')", name="ck_assets_asset_class"),
    )
    asset_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    asset_class: Mapped[str] = mapped_column(String, nullable=False)


class VenueRow(Base):
    __tablename__ = "venues"
    venue_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)


class InstrumentRow(Base):
    __tablename__ = "instruments"
    instrument_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.asset_id"), nullable=False, index=True
    )
    venue_id: Mapped[UUID] = mapped_column(
        ForeignKey("venues.venue_id"), nullable=False, index=True
    )


class ExternalIdentifierRow(Base):
    __tablename__ = "external_identifiers"
    __table_args__ = (
        UniqueConstraint(
            "instrument_id",
            "namespace",
            "value",
            "valid_from",
            name="uq_external_identifiers_interval",
        ),
        CheckConstraint(
            "valid_to IS NULL OR valid_to > valid_from", name="ck_external_identifiers_interval"
        ),
    )
    identifier_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.instrument_id"), nullable=False, index=True
    )
    namespace: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
