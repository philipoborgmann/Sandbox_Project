"""Canonical price series access port; revision writes require a new series ID."""

from typing import Protocol
from uuid import UUID

from .domain import PriceBar


class MarketDataRepository(Protocol):
    def save_bar(self, bar: PriceBar) -> None: ...
    def list_bars(self, series_id: UUID) -> tuple[PriceBar, ...]: ...
