"""Canonical market and macro observations, without provider schemas."""

from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quont_sandbox.common import Frequency, ObservationTime, to_utc


class AdjustmentPolicy(StrEnum):
    UNADJUSTED = "unadjusted"
    PROVIDER_ADJUSTED = "provider_adjusted"
    INTERNALLY_ADJUSTED = "internally_adjusted"


class ReturnMethod(StrEnum):
    SIMPLE = "simple"
    LOG = "log"


class PriceBar(BaseModel):
    """One OHLCV observation; missing fields remain None.

    series_id separates price series by source and adjustment policy.
    Price units are quote currency; volume units are the instrument's units.
    """

    model_config = ConfigDict(frozen=True, strict=True, extra="forbid", allow_inf_nan=False)
    instrument_id: UUID
    series_id: UUID
    frequency: Frequency
    time: ObservationTime
    adjustment_policy: AdjustmentPolicy
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def valid_bar(self) -> Self:
        self.time.validate_frequency(self.frequency)
        if self.high is not None and self.low is not None and self.high < self.low:
            raise ValueError("high must be at least low")
        for price in (self.open, self.close):
            if price is not None:
                if self.high is not None and price > self.high:
                    raise ValueError("open/close must not exceed high")
                if self.low is not None and price < self.low:
                    raise ValueError("open/close must not be below low")
        return self


class Quote(BaseModel):
    """A separate instantaneous bid/ask observation; sizes are instrument units.

    Crossed quotes are preserved for future quality analysis rather than rejected
    as a domain error. Missing bid/ask values remain explicit.
    """

    model_config = ConfigDict(frozen=True, strict=True, extra="forbid", allow_inf_nan=False)
    instrument_id: UUID
    venue_id: UUID
    timestamp: datetime
    bid_price: float | None
    ask_price: float | None
    bid_size: float | None = Field(default=None, ge=0)
    ask_size: float | None = Field(default=None, ge=0)

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return to_utc(value)


class ReturnObservation(BaseModel):
    """Derived fractional return with explicit source and methodology identity."""

    model_config = ConfigDict(frozen=True, strict=True, extra="forbid", allow_inf_nan=False)
    source_series_id: UUID
    frequency: Frequency
    time: ObservationTime
    value: float | None
    method: ReturnMethod
    adjustment_policy: AdjustmentPolicy
    processing_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_time(self) -> Self:
        self.time.validate_frequency(self.frequency)
        return self


class MacroSeries(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    series_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    frequency: Frequency


class MacroObservation(BaseModel):
    """Publication/availability are explicit; revisions receive distinct IDs."""

    model_config = ConfigDict(frozen=True, strict=True, extra="forbid", allow_inf_nan=False)
    observation_id: UUID = Field(default_factory=uuid4)
    series_id: UUID
    time: ObservationTime
    value: float | None
    published_at: datetime
    available_from: datetime

    @field_validator("published_at", "available_from")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return to_utc(value)

    @model_validator(mode="after")
    def valid_availability(self) -> Self:
        if self.available_from < self.published_at:
            raise ValueError("available_from must not precede publication")
        return self
