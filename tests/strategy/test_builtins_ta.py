"""Tests for technical analysis built-in functions."""

from decimal import Decimal

import pytest

from finsaas.core.series import Series
from finsaas.strategy.builtins.ta import (
    atr,
    barsince,
    bb,
    bbw,
    cci,
    change,
    correlation,
    cross,
    crossover,
    crossunder,
    cum,
    dmi,
    ema,
    falling,
    highest,
    highestbars,
    hma,
    kc,
    kcw,
    linreg,
    lowest,
    lowestbars,
    median,
    mfi,
    mom,
    obv,
    pivothigh,
    pivotlow,
    rising,
    rma,
    roc,
    rsi,
    sar,
    sma,
    smma,
    stdev,
    stoch,
    supertrend,
    valuewhen,
    variance,
    vwap,
    vwma,
    wma,
    wpr,
)


def _make_series(values, name="test"):
    """Helper: create a Series with committed values, last value as current."""
    s = Series(name=name)
    for v in values[:-1]:
        s.current = Decimal(str(v))
        s.commit()
    s.current = Decimal(str(values[-1]))
    return s


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


# ── Faz 1 Tests ──────────────────────────────────────────────────────


class TestSMMA:
    def test_smma_delegates_to_rma(self):
        s = _make_series([10, 20, 30, 40, 50])
        assert smma(s, 3) == rma(s, 3)

    def test_smma_insufficient_data(self):
        s = _make_series([10])
        result = smma(s, 10)
        assert isinstance(result, Decimal)

    def test_smma_length_1(self):
        s = _make_series([10, 20, 30])
        result = smma(s, 1)
        assert result == Decimal("30")


class TestCross:
    def test_cross_detects_crossover(self):
        s1 = Series(name="a")
        s2 = Series(name="b")
        s1.current = Decimal("10"); s2.current = Decimal("12")
        s1.commit(); s2.commit()
        s1.current = Decimal("15"); s2.current = Decimal("12")
        assert cross(s1, s2) is True

    def test_cross_detects_crossunder(self):
        s1 = Series(name="a")
        s2 = Series(name="b")
        s1.current = Decimal("15"); s2.current = Decimal("12")
        s1.commit(); s2.commit()
        s1.current = Decimal("10"); s2.current = Decimal("12")
        assert cross(s1, s2) is True

    def test_cross_no_cross(self):
        s1 = Series(name="a")
        s2 = Series(name="b")
        s1.current = Decimal("15"); s2.current = Decimal("12")
        s1.commit(); s2.commit()
        s1.current = Decimal("16"); s2.current = Decimal("12")
        assert cross(s1, s2) is False


class TestMom:
    def test_mom_basic(self):
        s = _make_series([100, 110, 120])
        assert mom(s, 2) == Decimal("20")  # 120 - 100

    def test_mom_insufficient_data(self):
        s = _make_series([100])
        assert mom(s, 5) == Decimal("0")

    def test_mom_length_1(self):
        s = _make_series([50, 60])
        assert mom(s, 1) == Decimal("10")


class TestROC:
    def test_roc_basic(self):
        s = _make_series([100, 120])
        result = roc(s, 1)
        assert result == Decimal("20")  # 100 * (120-100)/100

    def test_roc_insufficient_data(self):
        s = _make_series([100])
        assert roc(s, 5) == Decimal("0")

    def test_roc_zero_previous(self):
        s = _make_series([0, 10])
        assert roc(s, 1) == Decimal("0")


# ── Faz 2 Tests ──────────────────────────────────────────────────────


class TestWMA:
    def test_wma_basic(self):
        s = _make_series([10, 20, 30])
        # weights: 3, 2, 1 for current, [1], [2]
        # (30*3 + 20*2 + 10*1) / (3+2+1) = (90+40+10)/6 = 140/6
        result = wma(s, 3)
        expected = Decimal("140") / Decimal("6")
        assert abs(result - expected) < Decimal("0.0001")

    def test_wma_insufficient_data(self):
        s = _make_series([10])
        assert wma(s, 5) == Decimal("0")

    def test_wma_length_1(self):
        s = _make_series([10, 20, 30])
        assert wma(s, 1) == Decimal("30")


class TestHMA:
    def test_hma_basic(self):
        s = _make_series([10, 20, 30, 40, 50])
        result = hma(s, 4)
        assert isinstance(result, Decimal)
        # HMA should be responsive — closer to recent values
        assert result > Decimal("0")

    def test_hma_insufficient_data(self):
        s = _make_series([10])
        result = hma(s, 4)
        assert isinstance(result, Decimal)

    def test_hma_length_2(self):
        s = _make_series([10, 20, 30])
        result = hma(s, 2)
        assert isinstance(result, Decimal)


class TestVWMA:
    def test_vwma_basic(self):
        price = _make_series([100, 200, 300])
        vol = _make_series([10, 20, 30])
        result = vwma(price, vol, 3)
        # (300*30 + 200*20 + 100*10) / (30+20+10) = (9000+4000+1000)/60 = 233.33
        expected = Decimal("14000") / Decimal("60")
        assert abs(result - expected) < Decimal("0.01")

    def test_vwma_insufficient_data(self):
        price = _make_series([100])
        vol = _make_series([10])
        assert vwma(price, vol, 5) == Decimal("0")

    def test_vwma_zero_volume(self):
        price = _make_series([100, 200, 300])
        vol = _make_series([0, 0, 0])
        assert vwma(price, vol, 3) == Decimal("0")


# ── Faz 3 Tests ──────────────────────────────────────────────────────


class TestStoch:
    def test_stoch_basic(self):
        high = _make_series([12, 14, 13, 15, 14])
        low = _make_series([10, 11, 10, 12, 11])
        close = _make_series([11, 13, 12, 14, 13])
        result = stoch(close, high, low, 5)
        # highest high = 15, lowest low = 10
        # stoch = 100 * (13 - 10) / (15 - 10) = 60
        assert result == Decimal("60")

    def test_stoch_range_zero(self):
        high = _make_series([10, 10, 10])
        low = _make_series([10, 10, 10])
        close = _make_series([10, 10, 10])
        assert stoch(close, high, low, 3) == Decimal("0")

    def test_stoch_at_high(self):
        high = _make_series([10, 20, 15])
        low = _make_series([5, 10, 10])
        close = _make_series([8, 18, 20])  # close=highest=20
        result = stoch(close, high, low, 3)
        assert result == Decimal("100")


class TestPivotHigh:
    def test_pivothigh_detected(self):
        # Build: [5, 7, 10, 8, 6] — peak at index 2 (value 10)
        # With leftbars=2, rightbars=2, the candidate is at offset 2 from current
        s = _make_series([5, 7, 10, 8, 6])
        result = pivothigh(s, 2, 2)
        assert result == Decimal("10")

    def test_pivothigh_not_detected(self):
        s = _make_series([5, 7, 10, 11, 6])
        result = pivothigh(s, 2, 2)
        assert result is None

    def test_pivothigh_insufficient_data(self):
        s = _make_series([5, 7])
        assert pivothigh(s, 3, 3) is None

    def test_pivothigh_equal_neighbors(self):
        s = _make_series([10, 10, 10, 10, 10])
        result = pivothigh(s, 2, 2)
        assert result == Decimal("10")


class TestPivotLow:
    def test_pivotlow_detected(self):
        s = _make_series([10, 8, 5, 7, 9])
        result = pivotlow(s, 2, 2)
        assert result == Decimal("5")

    def test_pivotlow_not_detected(self):
        s = _make_series([10, 8, 5, 4, 9])
        result = pivotlow(s, 2, 2)
        assert result is None

    def test_pivotlow_insufficient_data(self):
        s = _make_series([5, 7])
        assert pivotlow(s, 3, 3) is None


# ── Faz 4 Tests ──────────────────────────────────────────────────────


class TestDMI:
    def test_dmi_basic(self):
        high = _make_series([i + 1 for i in range(20)])
        low = _make_series([i for i in range(20)])
        close = _make_series([i + Decimal("0.5") for i in range(20)])
        plus_di, minus_di, adx = dmi(high, low, close, 14)
        assert plus_di >= Decimal("0")
        assert minus_di >= Decimal("0")
        assert adx >= Decimal("0")

    def test_dmi_insufficient_data(self):
        high = _make_series([10, 12])
        low = _make_series([8, 9])
        close = _make_series([9, 11])
        plus_di, minus_di, adx = dmi(high, low, close, 14)
        assert plus_di == Decimal("0")
        assert minus_di == Decimal("0")

    def test_dmi_trending_up(self):
        high = _make_series([10 + i * 2 for i in range(20)])
        low = _make_series([8 + i * 2 for i in range(20)])
        close = _make_series([9 + i * 2 for i in range(20)])
        plus_di, minus_di, _ = dmi(high, low, close, 14)
        assert plus_di > minus_di

    def test_dmi_returns_tuple_of_three(self):
        high = _make_series([10 + i for i in range(20)])
        low = _make_series([8 + i for i in range(20)])
        close = _make_series([9 + i for i in range(20)])
        result = dmi(high, low, close)
        assert len(result) == 3


class TestLinreg:
    def test_linreg_perfect_line(self):
        # y = x: [0, 1, 2, 3, 4]
        s = _make_series([0, 1, 2, 3, 4])
        result = linreg(s, 5)
        # Should evaluate at the newest point (x=4), value should be ~4
        assert abs(result - Decimal("4")) < Decimal("0.001")

    def test_linreg_constant(self):
        s = _make_series([10, 10, 10, 10, 10])
        result = linreg(s, 5)
        assert abs(result - Decimal("10")) < Decimal("0.001")

    def test_linreg_with_offset(self):
        s = _make_series([0, 1, 2, 3, 4])
        result = linreg(s, 5, offset=1)
        # Should evaluate at x=3
        assert abs(result - Decimal("3")) < Decimal("0.001")

    def test_linreg_insufficient_data(self):
        s = _make_series([10])
        assert linreg(s, 5) == Decimal("0")


# ── Faz 5 Tests ──────────────────────────────────────────────────────


class TestCCI:
    def test_cci_basic(self):
        s = _make_series([i for i in range(25)])
        result = cci(s, 20)
        assert isinstance(result, Decimal)

    def test_cci_constant_prices(self):
        s = _make_series([100] * 25)
        result = cci(s, 20)
        assert result == Decimal("0")  # No deviation

    def test_cci_insufficient_data(self):
        s = _make_series([100])
        assert cci(s, 20) == Decimal("0")


class TestMFI:
    def test_mfi_basic(self):
        high = _make_series([10 + i for i in range(20)])
        low = _make_series([8 + i for i in range(20)])
        close = _make_series([9 + i for i in range(20)])
        vol = _make_series([1000] * 20)
        result = mfi(high, low, close, vol, 14)
        assert Decimal("0") <= result <= Decimal("100")

    def test_mfi_insufficient_data(self):
        high = _make_series([10, 12])
        low = _make_series([8, 9])
        close = _make_series([9, 11])
        vol = _make_series([1000, 1000])
        result = mfi(high, low, close, vol, 14)
        assert result == Decimal("50")

    def test_mfi_all_up(self):
        high = _make_series([10 + i * 3 for i in range(20)])
        low = _make_series([8 + i * 3 for i in range(20)])
        close = _make_series([9 + i * 3 for i in range(20)])
        vol = _make_series([1000] * 20)
        result = mfi(high, low, close, vol, 14)
        assert result == Decimal("100")


class TestWPR:
    def test_wpr_basic(self):
        high = _make_series([12, 14, 13, 15, 14])
        low = _make_series([10, 11, 10, 12, 11])
        close = _make_series([11, 13, 12, 14, 13])
        result = wpr(high, low, close, 5)
        # -100 * (15 - 13) / (15 - 10) = -100 * 2/5 = -40
        assert result == Decimal("-40")

    def test_wpr_at_high(self):
        high = _make_series([10, 20, 15])
        low = _make_series([5, 10, 10])
        close = _make_series([8, 18, 20])
        result = wpr(high, low, close, 3)
        assert result == Decimal("0")  # close == highest

    def test_wpr_range_zero(self):
        high = _make_series([10, 10, 10])
        low = _make_series([10, 10, 10])
        close = _make_series([10, 10, 10])
        assert wpr(high, low, close, 3) == Decimal("0")


class TestOBV:
    def test_obv_basic(self):
        close = _make_series([100, 110, 105, 115])
        vol = _make_series([1000, 2000, 1500, 2500])
        result = obv(close, vol)
        assert isinstance(result, Decimal)

    def test_obv_all_up(self):
        close = _make_series([100, 110, 120])
        vol = _make_series([1000, 1000, 1000])
        result = obv(close, vol)
        assert result > Decimal("0")

    def test_obv_all_down(self):
        close = _make_series([120, 110, 100])
        vol = _make_series([1000, 1000, 1000])
        result = obv(close, vol)
        assert result < Decimal("0")


class TestVWAP:
    def test_vwap_basic(self):
        high = _make_series([12, 14, 13])
        low = _make_series([10, 11, 10])
        close = _make_series([11, 13, 12])
        vol = _make_series([100, 200, 150])
        result = vwap(high, low, close, vol)
        assert result > Decimal("0")

    def test_vwap_zero_volume(self):
        high = _make_series([12, 14])
        low = _make_series([10, 11])
        close = _make_series([11, 13])
        vol = _make_series([0, 0])
        assert vwap(high, low, close, vol) == Decimal("0")

    def test_vwap_single_bar(self):
        high = _make_series([15])
        low = _make_series([10])
        close = _make_series([12])
        vol = _make_series([100])
        result = vwap(high, low, close, vol)
        # typical_price = (15+10+12)/3
        expected_tp = (Decimal("15") + Decimal("10") + Decimal("12")) / Decimal("3")
        assert abs(result - expected_tp) < Decimal("0.01")


class TestCum:
    def test_cum_basic(self):
        s = _make_series([10, 20, 30])
        result = cum(s)
        assert result == Decimal("60")

    def test_cum_single(self):
        s = _make_series([42])
        result = cum(s)
        assert result == Decimal("42")

    def test_cum_with_negatives(self):
        s = _make_series([10, -5, 20])
        result = cum(s)
        assert result == Decimal("25")


# ── Faz 6 Tests ──────────────────────────────────────────────────────


class TestKC:
    def test_kc_basic(self):
        s = _make_series([100 + i for i in range(25)])
        upper, middle, lower = kc(s, 20, Decimal("1.5"), 10)
        assert upper > middle > lower

    def test_kc_with_hlc(self):
        high = _make_series([100 + i * 2 for i in range(25)])
        low = _make_series([98 + i * 2 for i in range(25)])
        close = _make_series([99 + i * 2 for i in range(25)])
        upper, middle, lower = kc(close, 20, Decimal("2"), 10, high, low, close)
        assert upper > middle > lower

    def test_kc_returns_three_values(self):
        s = _make_series([100] * 25)
        result = kc(s, 20, Decimal("2"), 10)
        assert len(result) == 3


class TestSupertrend:
    def test_supertrend_basic(self):
        high = _make_series([10 + i for i in range(20)])
        low = _make_series([8 + i for i in range(20)])
        close = _make_series([9 + i for i in range(20)])
        value, direction = supertrend(high, low, close, Decimal("3"), 10)
        assert isinstance(value, Decimal)
        assert direction in (1, -1)

    def test_supertrend_uptrend(self):
        high = _make_series([10 + i * 2 for i in range(20)])
        low = _make_series([8 + i * 2 for i in range(20)])
        # close near the high to ensure close > hl2
        close = _make_series([10 + i * 2 for i in range(20)])
        _, direction = supertrend(high, low, close, Decimal("3"), 10)
        # close == high > hl2, so bullish
        assert direction == 1

    def test_supertrend_downtrend(self):
        high = _make_series([100 - i * 2 for i in range(20)])
        low = _make_series([98 - i * 2 for i in range(20)])
        close = _make_series([99 - i * 2 for i in range(20)])
        _, direction = supertrend(high, low, close, Decimal("3"), 10)
        assert direction in (1, -1)


class TestSAR:
    def test_sar_basic(self):
        high = _make_series([10 + i for i in range(10)])
        low = _make_series([8 + i for i in range(10)])
        result = sar(high, low)
        assert isinstance(result, Decimal)

    def test_sar_insufficient_data(self):
        high = _make_series([10])
        low = _make_series([8])
        result = sar(high, low)
        assert result == Decimal("8")

    def test_sar_custom_params(self):
        high = _make_series([10 + i for i in range(10)])
        low = _make_series([8 + i for i in range(10)])
        result = sar(high, low, Decimal("0.01"), Decimal("0.01"), Decimal("0.1"))
        assert isinstance(result, Decimal)


# ── Faz 7 Tests ──────────────────────────────────────────────────────


class TestRising:
    def test_rising_true(self):
        s = _make_series([10, 20, 30, 40])
        assert rising(s, 3) is True

    def test_rising_false(self):
        s = _make_series([10, 20, 15, 40])
        assert rising(s, 3) is False

    def test_rising_insufficient_data(self):
        s = _make_series([10])
        assert rising(s, 3) is False


class TestFalling:
    def test_falling_true(self):
        s = _make_series([40, 30, 20, 10])
        assert falling(s, 3) is True

    def test_falling_false(self):
        s = _make_series([40, 30, 35, 10])
        assert falling(s, 3) is False

    def test_falling_insufficient_data(self):
        s = _make_series([10])
        assert falling(s, 3) is False


class TestVariance:
    def test_variance_basic(self):
        s = _make_series([10, 20, 30, 40, 50])
        result = variance(s, 5)
        sd = stdev(s, 5)
        assert abs(result - sd * sd) < Decimal("0.0001")

    def test_variance_constant(self):
        s = _make_series([10, 10, 10])
        assert variance(s, 3) == Decimal("0")

    def test_variance_insufficient_data(self):
        s = _make_series([10])
        assert variance(s, 5) == Decimal("0")


class TestMedian:
    def test_median_odd(self):
        s = _make_series([30, 10, 50, 20, 40])
        result = median(s, 5)
        assert result == Decimal("30")

    def test_median_even(self):
        s = _make_series([10, 30, 20, 40])
        result = median(s, 4)
        assert result == Decimal("25")  # (20+30)/2

    def test_median_insufficient_data(self):
        s = _make_series([10])
        assert median(s, 5) == Decimal("0")


class TestCorrelation:
    def test_correlation_perfect_positive(self):
        s1 = _make_series([1, 2, 3, 4, 5])
        s2 = _make_series([10, 20, 30, 40, 50])
        result = correlation(s1, s2, 5)
        assert abs(result - Decimal("1")) < Decimal("0.001")

    def test_correlation_perfect_negative(self):
        s1 = _make_series([1, 2, 3, 4, 5])
        s2 = _make_series([50, 40, 30, 20, 10])
        result = correlation(s1, s2, 5)
        assert abs(result + Decimal("1")) < Decimal("0.001")

    def test_correlation_insufficient_data(self):
        s1 = _make_series([1])
        s2 = _make_series([2])
        assert correlation(s1, s2, 5) == Decimal("0")


class TestHighestBars:
    def test_highestbars_basic(self):
        s = _make_series([5, 10, 3, 8, 6])
        result = highestbars(s, 5)
        # 10 is at index 3 from current (s[3])
        assert result == -3

    def test_highestbars_current_is_highest(self):
        s = _make_series([5, 3, 8, 6, 15])
        assert highestbars(s, 5) == 0

    def test_highestbars_length_1(self):
        s = _make_series([5, 10, 3])
        assert highestbars(s, 1) == 0


class TestLowestBars:
    def test_lowestbars_basic(self):
        s = _make_series([5, 10, 3, 8, 6])
        result = lowestbars(s, 5)
        # 3 is at index 2 from current (s[2])
        assert result == -2

    def test_lowestbars_current_is_lowest(self):
        s = _make_series([15, 10, 8, 6, 2])
        assert lowestbars(s, 5) == 0

    def test_lowestbars_length_1(self):
        s = _make_series([5, 10, 3])
        assert lowestbars(s, 1) == 0


class TestBBW:
    def test_bbw_basic(self):
        s = _make_series([100 + i % 5 for i in range(25)])
        result = bbw(s, 20)
        assert result > Decimal("0")

    def test_bbw_constant(self):
        s = _make_series([100] * 25)
        result = bbw(s, 20)
        assert result == Decimal("0")

    def test_bbw_insufficient_data(self):
        s = _make_series([100])
        result = bbw(s, 20)
        assert isinstance(result, Decimal)


class TestKCW:
    def test_kcw_basic(self):
        s = _make_series([100 + i for i in range(25)])
        result = kcw(s, 20, Decimal("1.5"), 10)
        assert result > Decimal("0")

    def test_kcw_constant(self):
        s = _make_series([100] * 25)
        result = kcw(s, 20, Decimal("2"), 10)
        assert result == Decimal("0")


class TestBarsince:
    def test_barsince_current_true(self):
        s = Series(name="cond")
        s.current = True
        s.commit()
        s.current = True
        assert barsince(s) == 0

    def test_barsince_past_true(self):
        s = Series(name="cond")
        s.current = True
        s.commit()
        s.current = False
        s.commit()
        s.current = False
        assert barsince(s) == 2

    def test_barsince_never_true(self):
        s = Series(name="cond")
        s.current = False
        s.commit()
        s.current = False
        assert barsince(s) == -1


class TestValuewhen:
    def test_valuewhen_basic(self):
        cond = Series(name="cond")
        src = Series(name="src")
        for c, v in [(False, 10), (True, 20), (False, 30)]:
            cond.current = c
            src.current = Decimal(str(v))
            cond.commit()
            src.commit()
        cond.current = False
        src.current = Decimal("40")
        result = valuewhen(cond, src, 0)
        assert result == Decimal("20")

    def test_valuewhen_occurrence_1(self):
        cond = Series(name="cond")
        src = Series(name="src")
        for c, v in [(True, 10), (False, 20), (True, 30), (False, 40)]:
            cond.current = c
            src.current = Decimal(str(v))
            cond.commit()
            src.commit()
        cond.current = False
        src.current = Decimal("50")
        result = valuewhen(cond, src, 1)
        assert result == Decimal("10")

    def test_valuewhen_not_found(self):
        cond = Series(name="cond")
        src = Series(name="src")
        cond.current = False
        src.current = Decimal("10")
        cond.commit()
        src.commit()
        cond.current = False
        src.current = Decimal("20")
        assert valuewhen(cond, src, 0) == Decimal("0")
