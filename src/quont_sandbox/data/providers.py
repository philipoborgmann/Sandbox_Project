"""Provider port accepts canonical requests for a separately selected venue."""

from typing import Protocol, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quont_sandbox.common import Frequency, ObservationTime

from .domain import AdjustmentPolicy, PriceBar


class Provider(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    provider_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)


class MarketDataRequest(BaseModel):
    """Inclusive start, exclusive end in the requested frequency's time representation."""

    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    instrument_id: UUID
    venue_id: UUID
    frequency: Frequency
    adjustment_policy: AdjustmentPolicy
    start: ObservationTime
    end: ObservationTime

    @model_validator(mode="after")
    def valid_range(self) -> Self:
        self.start.validate_frequency(self.frequency)
        self.end.validate_frequency(self.frequency)
        if self.start.timestamp is not None and self.end.timestamp is not None:
            valid = self.start.timestamp < self.end.timestamp
        elif self.start.trading_date is not None and self.end.trading_date is not None:
            valid = self.start.trading_date < self.end.trading_date
        elif self.start.period is not None and self.end.period is not None:
            valid = (self.start.period.year, self.start.period.month) < (
                self.end.period.year,
                self.end.period.month,
            )
        else:
            valid = False
        if not valid:
            raise ValueError("end must be later than start")
        return self


class MarketDataProvider(Protocol):
    @property
    def identity(self) -> Provider: ...
    def fetch_bars(self, request: MarketDataRequest) -> tuple[PriceBar, ...]: ...
