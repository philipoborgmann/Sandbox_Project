from datetime import UTC, date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError as PydanticValidationError

from quont_sandbox.common import Frequency, MonthlyPeriod, ObservationTime, ValidationError, to_utc
from quont_sandbox.data import (
    AdjustmentPolicy,
    MacroObservation,
    MacroSeries,
    MarketDataRepository,
    PriceBar,
    Quote,
    ReturnMethod,
    ReturnObservation,
)
from quont_sandbox.data.infrastructure.memory import InMemoryMarketDataRepository


def daily_bar() -> PriceBar:
    return PriceBar(
        instrument_id=uuid4(),
        series_id=uuid4(),
        frequency=Frequency.DAILY,
        time=ObservationTime(trading_date=date(2024, 1, 2)),
        adjustment_policy=AdjustmentPolicy.UNADJUSTED,
        open=100.0,
        high=110.0,
        low=95.0,
        close=105.0,
        volume=42.0,
    )


def test_bar_validation_and_missing_values() -> None:
    bar = daily_bar()
    assert bar.time.timestamp is None
    missing = PriceBar.model_validate(
        bar.model_dump() | {"time": bar.time, "open": None, "volume": None}
    )
    assert missing.open is None and missing.volume is None
    for changes in (
        {"high": 90.0},
        {"low": 106.0},
        {"open": 120.0},
        {"close": 90.0},
        {"volume": -1.0},
        {"close": float("nan")},
        {"open": float("inf")},
    ):
        with pytest.raises(PydanticValidationError):
            PriceBar.model_validate(bar.model_dump() | {"time": bar.time} | changes)


def test_time_semantics() -> None:
    local = datetime(2024, 1, 2, 10, tzinfo=timezone(timedelta(hours=2)))
    assert to_utc(local) == datetime(2024, 1, 2, 8, tzinfo=UTC)
    intraday = ObservationTime(timestamp=local)
    intraday.validate_frequency(Frequency.HOUR_1)
    assert intraday.timestamp is not None and intraday.timestamp.tzinfo == UTC
    with pytest.raises(ValueError, match="timezone-aware"):
        to_utc(datetime(2024, 1, 2))
    with pytest.raises(PydanticValidationError):
        ObservationTime(timestamp=datetime(2024, 1, 2))
    with pytest.raises(PydanticValidationError):
        ObservationTime()
    with pytest.raises(PydanticValidationError):
        ObservationTime(timestamp=local, trading_date=date(2024, 1, 2))
    with pytest.raises(PydanticValidationError):
        ObservationTime(trading_date=local)
    month = ObservationTime(period=MonthlyPeriod(year=2024, month=2))
    month.validate_frequency(Frequency.MONTHLY)
    assert month.timestamp is None and month.trading_date is None
    with pytest.raises(ValueError, match="frequency"):
        month.validate_frequency(Frequency.DAILY)
    with pytest.raises(PydanticValidationError):
        MonthlyPeriod(year=2024, month=13)
    bar = daily_bar()
    with pytest.raises(PydanticValidationError):
        PriceBar.model_validate(bar.model_dump() | {"time": intraday})
    monthly_bar = PriceBar.model_validate(
        bar.model_dump() | {"frequency": Frequency.MONTHLY, "time": month}
    )
    assert monthly_bar.time.period == MonthlyPeriod(year=2024, month=2)


def test_quotes_remain_separate_and_preserve_missing_or_crossed_prices() -> None:
    quote = Quote(
        instrument_id=uuid4(),
        venue_id=uuid4(),
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
        bid_price=101.0,
        ask_price=100.0,
    )
    assert quote.bid_size is None
    for changes in (
        {"timestamp": datetime(2024, 1, 2)},
        {"ask_size": -1.0},
        {"bid_price": float("nan")},
        {"ask_price": float("inf")},
    ):
        with pytest.raises(PydanticValidationError):
            Quote.model_validate(quote.model_dump() | changes)
    missing = Quote.model_validate(quote.model_dump() | {"bid_price": None})
    assert missing.bid_price is None


def test_return_and_macro_metadata() -> None:
    time = ObservationTime(period=MonthlyPeriod(year=2024, month=1))
    result = ReturnObservation(
        source_series_id=uuid4(),
        frequency=Frequency.MONTHLY,
        time=time,
        value=0.1,
        method=ReturnMethod.SIMPLE,
        adjustment_policy=AdjustmentPolicy.PROVIDER_ADJUSTED,
        processing_version="v1",
    )
    assert result.value == 0.1
    series = MacroSeries(name="Synthetic CPI", unit="index", frequency=Frequency.MONTHLY)
    published = datetime(2024, 2, 1, tzinfo=UTC)
    observation = MacroObservation(
        series_id=series.series_id,
        time=time,
        value=None,
        published_at=published,
        available_from=published,
    )
    assert observation.value is None
    assert "asset_id" not in MacroSeries.model_fields
    with pytest.raises(PydanticValidationError):
        MacroObservation(
            series_id=series.series_id,
            time=time,
            value=100.0,
            published_at=published,
            available_from=published - timedelta(days=1),
        )


def test_bar_repository_is_append_only_and_series_consistent() -> None:
    repository: MarketDataRepository = InMemoryMarketDataRepository()
    bar = daily_bar()
    repository.save_bar(bar)
    repository.save_bar(bar)
    assert repository.list_bars(bar.series_id) == (bar,)
    assert repository.list_bars(uuid4()) == ()
    revised = PriceBar.model_validate(bar.model_dump() | {"time": bar.time, "close": 106.0})
    with pytest.raises(ValidationError, match="Revised"):
        repository.save_bar(revised)
    inconsistent = PriceBar.model_validate(
        bar.model_dump() | {"time": bar.time, "instrument_id": uuid4()}
    )
    with pytest.raises(ValidationError, match="one instrument"):
        repository.save_bar(inconsistent)
    next_bar = PriceBar.model_validate(
        bar.model_dump() | {"time": ObservationTime(trading_date=date(2024, 1, 3))}
    )
    repository.save_bar(next_bar)
    assert repository.list_bars(bar.series_id) == (bar, next_bar)
