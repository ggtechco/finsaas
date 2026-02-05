"""Tests for technical analysis built-in functions."""

from decimal import Decimal

import pytest

from finsaas.core.series import Series
from finsaas.strategy.builtins.ta import (
    atr,
    bb,
    change,
    crossover,
    crossunder,
    ema,
    highest,
    lowest,
    rsi,
    sma,
    stdev,
)


@pytest.fixture
def price_series() -> Series[Decimal]:
    """A series with known values for testing indicators."""
    s: Series[Decimal] = Series(max_bars_back=100, name="close")
    values = [
        Decimal("44"), Decimal("44.34"), Decimal("44.09"), Decimal("43.61"),
        Decimal("44.33"), Decimal("44.83"), Decimal("45.10"), Decimal("45.42"),
        Decimal("45.84"), Decimal("46.08"), Decimal("45.89"), Decimal("46.03"),
        Decimal("45.61"), Decimal("46.28"), Decimal("46.28"), Decimal("46.00"),
        Decimal("46.03"), Decimal("46.41"), Decimal("46.22"), Decimal("45.64"),
    ]
    for v in values:
        s.current = v
        s.commit()
    return s


class TestSMA:
    def test_sma_basic(self):
        s: Series[Decimal] = Series(name="test")
        for v in [Decimal("10"), Decimal("20"), Decimal("30")]:
            s.current = v
            s.commit()
        s.current = Decimal("40")
        result = sma(s, 4)
        # (40 + 30 + 20 + 10) / 4 = 25
        assert result == Decimal("25")

    def test_sma_length_1(self):
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("42")
        s.commit()
        s.current = Decimal("50")
        result = sma(s, 1)
        assert result == Decimal("50")

    def test_sma_insufficient_data(self):
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("100")
        result = sma(s, 10)
        assert result == Decimal("0")


class TestEMA:
    def test_ema_single_value(self):
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("100")
        result = ema(s, 10)
        assert result == Decimal("100")

    def test_ema_converges(self):
        """EMA should approach the mean for constant values."""
        s: Series[Decimal] = Series(name="test")
        for _ in range(50):
            s.current = Decimal("100")
            s.commit()
        s.current = Decimal("100")
        result = ema(s, 10)
        assert abs(result - Decimal("100")) < Decimal("1")


class TestRSI:
    def test_rsi_neutral_default(self):
        """RSI should return 50 with insufficient data."""
        s: Series[Decimal] = Series(name="test")
        for v in [Decimal("100"), Decimal("101")]:
            s.current = v
            s.commit()
        s.current = Decimal("102")
        result = rsi(s, 14)
        assert result == Decimal("50")

    def test_rsi_with_data(self, price_series):
        price_series.current = Decimal("46.00")
        result = rsi(price_series, 14)
        # RSI should be between 0 and 100
        assert Decimal("0") <= result <= Decimal("100")

    def test_rsi_all_gains(self):
        """RSI should be 100 when all changes are positive."""
        s: Series[Decimal] = Series(name="test")
        for i in range(20):
            s.current = Decimal(str(100 + i))
            s.commit()
        s.current = Decimal("120")
        result = rsi(s, 14)
        assert result == Decimal("100")


class TestCrossover:
    def test_crossover_true(self):
        s1: Series[Decimal] = Series(name="fast")
        s2: Series[Decimal] = Series(name="slow")

        # Previous: s1 <= s2
        s1.current = Decimal("10")
        s2.current = Decimal("12")
        s1.commit()
        s2.commit()

        # Current: s1 > s2
        s1.current = Decimal("15")
        s2.current = Decimal("12")

        assert crossover(s1, s2) is True

    def test_crossover_false_no_cross(self):
        s1: Series[Decimal] = Series(name="fast")
        s2: Series[Decimal] = Series(name="slow")

        s1.current = Decimal("15")
        s2.current = Decimal("12")
        s1.commit()
        s2.commit()

        s1.current = Decimal("16")
        s2.current = Decimal("12")

        assert crossover(s1, s2) is False  # Was already above

    def test_crossunder_true(self):
        s1: Series[Decimal] = Series(name="fast")
        s2: Series[Decimal] = Series(name="slow")

        s1.current = Decimal("15")
        s2.current = Decimal("12")
        s1.commit()
        s2.commit()

        s1.current = Decimal("10")
        s2.current = Decimal("12")

        assert crossunder(s1, s2) is True


class TestHighestLowest:
    def test_highest(self):
        s: Series[Decimal] = Series(name="test")
        for v in [Decimal("5"), Decimal("10"), Decimal("3"), Decimal("8")]:
            s.current = v
            s.commit()
        s.current = Decimal("6")
        result = highest(s, 5)
        assert result == Decimal("10")

    def test_lowest(self):
        s: Series[Decimal] = Series(name="test")
        for v in [Decimal("5"), Decimal("10"), Decimal("3"), Decimal("8")]:
            s.current = v
            s.commit()
        s.current = Decimal("6")
        result = lowest(s, 5)
        assert result == Decimal("3")


class TestChange:
    def test_change_basic(self):
        s: Series[Decimal] = Series(name="test")
        s.current = Decimal("100")
        s.commit()
        s.current = Decimal("110")
        result = change(s, 1)
        assert result == Decimal("10")


class TestBB:
    def test_bollinger_bands(self):
        s: Series[Decimal] = Series(name="test")
        for i in range(25):
            s.current = Decimal(str(100 + i % 5))
            s.commit()
        s.current = Decimal("102")
        upper, middle, lower = bb(s, 20)
        assert upper > middle > lower
