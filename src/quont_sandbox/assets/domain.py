"""Stable asset identity independent of symbols, providers and persistence."""

from datetime import date
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quont_sandbox.common import AssetClass, ValidationError


class Asset(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    asset_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
    asset_class: AssetClass


class Venue(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    venue_id: UUID = Field(default_factory=uuid4)
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)


class Instrument(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    instrument_id: UUID = Field(default_factory=uuid4)
    asset_id: UUID
    venue_id: UUID


class ExternalIdentifier(BaseModel):
    """Instrument identifier in a namespace with a half-open validity interval.

    Examples: namespace='isin', or namespace='provider:<id>:symbol'.
    Identifier history is retained by assigning a new ID to each interval.
    """

    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    identifier_id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    namespace: str = Field(min_length=1)
    value: str = Field(min_length=1)
    valid_from: date
    valid_to: date | None = None

    @model_validator(mode="after")
    def valid_interval(self) -> Self:
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be later than valid_from")
        return self


def validate_identifier_update(existing: ExternalIdentifier, updated: ExternalIdentifier) -> None:
    """Identity/history fields remain fixed; an open validity interval can close once."""
    if existing == updated:
        return
    if (
        existing.valid_to is None
        and updated.valid_to is not None
        and existing.model_copy(update={"valid_to": updated.valid_to}) == updated
    ):
        return
    raise ValidationError("Identifier history fields are immutable; use a new interval ID")
