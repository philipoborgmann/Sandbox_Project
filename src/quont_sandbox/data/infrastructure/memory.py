"""Append-only in-memory canonical series adapter."""

from uuid import UUID

from quont_sandbox.common import ValidationError

from ..domain import PriceBar


class InMemoryMarketDataRepository:
    def __init__(self) -> None:
        self._bars: dict[UUID, list[PriceBar]] = {}

    def save_bar(self, bar: PriceBar) -> None:
        bars = self._bars.setdefault(bar.series_id, [])
        for existing in bars:
            if (existing.instrument_id, existing.frequency, existing.adjustment_policy) != (
                bar.instrument_id,
                bar.frequency,
                bar.adjustment_policy,
            ):
                raise ValidationError("A series must have one instrument, frequency and policy")
            if existing.time == bar.time:
                if existing == bar:
                    return
                raise ValidationError("Revised data requires a new source series ID")
        bars.append(bar)

    def list_bars(self, series_id: UUID) -> tuple[PriceBar, ...]:
        """Return observations in insertion order; no implicit resampling or filling."""
        return tuple(self._bars.get(series_id, ()))
