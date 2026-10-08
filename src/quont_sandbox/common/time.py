"""Absolute timestamps and calendar observations have different semantics."""

from datetime import UTC, date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .types import Frequency


def to_utc(value: datetime) -> datetime:
    """Reject ambiguous naive timestamps and normalize aware timestamps to UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("An absolute timestamp must be timezone-aware")
    return value.astimezone(UTC)


class MonthlyPeriod(BaseModel):
    """A calendar month, not an invented instant at midnight."""

    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    year: int = Field(ge=1, le=9999)
    month: int = Field(ge=1, le=12)


class ObservationTime(BaseModel):
    """Exactly one temporal identity; timestamps denote intraday bar starts."""

    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")
    timestamp: datetime | None = None
    trading_date: date | None = None
    period: MonthlyPeriod | None = None

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        return to_utc(value) if value is not None else None

    @model_validator(mode="after")
    def exactly_one(self) -> Self:
        if (
            sum(value is not None for value in (self.timestamp, self.trading_date, self.period))
            != 1
        ):
            raise ValueError("Choose exactly one of timestamp, trading_date, period")
        return self

    def validate_frequency(self, frequency: Frequency) -> None:
        if frequency == Frequency.DAILY:
            valid = self.trading_date is not None
        elif frequency == Frequency.MONTHLY:
            valid = self.period is not None
        else:
            valid = self.timestamp is not None
        if not valid:
            raise ValueError("Temporal identity does not match frequency")
