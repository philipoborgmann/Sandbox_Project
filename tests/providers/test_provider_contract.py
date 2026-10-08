from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from quont_sandbox.common import Frequency, ObservationTime
from quont_sandbox.data import (
    AdjustmentPolicy,
    MarketDataProvider,
    MarketDataRequest,
    PriceBar,
    Provider,
)


class FakeProvider:
    def __init__(self) -> None:
        self._identity = Provider(name="Synthetic provider")

    @property
    def identity(self) -> Provider:
        return self._identity

    def fetch_bars(self, request: MarketDataRequest) -> tuple[PriceBar, ...]:
        return ()


def test_provider_is_separate_from_requested_venue() -> None:
    provider: MarketDataProvider = FakeProvider()
    request = MarketDataRequest(
        instrument_id=uuid4(),
        venue_id=uuid4(),
        frequency=Frequency.DAILY,
        adjustment_policy=AdjustmentPolicy.UNADJUSTED,
        start=ObservationTime(trading_date=date(2024, 1, 1)),
        end=ObservationTime(trading_date=date(2024, 2, 1)),
    )
    assert provider.identity.provider_id != request.venue_id
    assert provider.fetch_bars(request) == ()
    assert "venue_id" not in Provider.model_fields
    with pytest.raises(ValidationError):
        MarketDataRequest.model_validate(
            request.model_dump() | {"start": request.start, "end": request.start}
        )
