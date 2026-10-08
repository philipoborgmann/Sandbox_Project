"""Controlled values shared by assets and data."""

from enum import StrEnum


class AssetClass(StrEnum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    CRYPTO = "CRYPTO"


class Frequency(StrEnum):
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    HOUR_1 = "1h"
    DAILY = "1d"
    MONTHLY = "1mo"
