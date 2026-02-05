"""Shared test fixtures."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from finsaas.core.series import Series
from finsaas.core.types import OHLCV, SymbolInfo, Timeframe
from finsaas.data.feed import CSVFeed, InMemoryFeed


FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_CSV = FIXTURES_DIR / "sample_ohlcv.csv"


@pytest.fixture
def sample_bars() -> list[OHLCV]:
    """Generate sample OHLCV bars for testing."""
    bars = []
    base_time = datetime(2023, 1, 1, 0, 0, 0)
    prices = [
        (100, 105, 98, 103, 1000),
        (103, 107, 102, 106, 1200),
        (106, 108, 104, 105, 800),
        (105, 110, 104, 109, 1500),
        (109, 112, 108, 111, 1300),
        (111, 113, 107, 108, 900),
        (108, 109, 105, 106, 1100),
        (106, 108, 103, 104, 1000),
        (104, 106, 101, 102, 1400),
        (102, 105, 100, 103, 1200),
    ]
    for i, (o, h, l, c, v) in enumerate(prices):
        bar = OHLCV(
            timestamp=datetime(2023, 1, 1, i, 0, 0),
            open=Decimal(str(o)),
            high=Decimal(str(h)),
            low=Decimal(str(l)),
            close=Decimal(str(c)),
            volume=Decimal(str(v)),
        )
        bars.append(bar)
    return bars


@pytest.fixture
def in_memory_feed(sample_bars: list[OHLCV]) -> InMemoryFeed:
    """Create an in-memory data feed from sample bars."""
    return InMemoryFeed(bars=sample_bars, symbol="TEST", timeframe="1h")


@pytest.fixture
def csv_feed() -> CSVFeed:
    """Create a CSV data feed from the sample file."""
    return CSVFeed(filepath=str(SAMPLE_CSV), symbol="TEST", timeframe="1h")


@pytest.fixture
def symbol_info() -> SymbolInfo:
    """Create a sample SymbolInfo."""
    return SymbolInfo(ticker="TEST", exchange="TEST_EXCHANGE")


@pytest.fixture
def decimal_series() -> Series[Decimal]:
    """Create a Series pre-populated with Decimal values."""
    s: Series[Decimal] = Series(max_bars_back=100, name="test")
    values = [Decimal("100"), Decimal("102"), Decimal("101"), Decimal("105"), Decimal("103")]
    for v in values:
        s.current = v
        s.commit()
    return s
