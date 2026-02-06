"""Pine Script runtime environment.

Provides the runtime context for executing transpiled Pine Script strategies.
Maps Pine Script built-in functions to their Python implementations.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from finsaas.core.series import Series, na, nz, fixnan
from finsaas.strategy.builtins import ta
from finsaas.strategy.builtins import math_funcs


class PineRuntime:
    """Runtime environment for transpiled Pine Script code.

    Provides access to built-in functions and variables
    in a way that matches Pine Script's semantics.
    """

    def __init__(self) -> None:
        self.ta = TaNamespace()
        self.math = MathNamespace()

    def nz(self, value: Any, replacement: Any = None) -> Any:
        return nz(value, replacement)

    def na(self, value: Any) -> bool:
        return na(value)

    def fixnan(self, series: Series) -> Any:  # type: ignore[type-arg]
        return fixnan(series)


class TaNamespace:
    """Namespace for ta.* functions."""

    def sma(self, source: Series[Decimal], length: int) -> Decimal:
        return ta.sma(source, length)

    def ema(self, source: Series[Decimal], length: int) -> Decimal:
        return ta.ema(source, length)

    def rsi(self, source: Series[Decimal], length: int = 14) -> Decimal:
        return ta.rsi(source, length)

    def macd(
        self,
        source: Series[Decimal],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> tuple[Decimal, Decimal, Decimal]:
        return ta.macd(source, fast, slow, signal)

    def crossover(self, s1: Series[Decimal], s2: Series[Decimal]) -> bool:
        return ta.crossover(s1, s2)

    def crossunder(self, s1: Series[Decimal], s2: Series[Decimal]) -> bool:
        return ta.crossunder(s1, s2)

    def highest(self, source: Series[Decimal], length: int) -> Decimal:
        return ta.highest(source, length)

    def lowest(self, source: Series[Decimal], length: int) -> Decimal:
        return ta.lowest(source, length)

    def atr(
        self,
        high: Series[Decimal],
        low: Series[Decimal],
        close: Series[Decimal],
        length: int = 14,
    ) -> Decimal:
        return ta.atr(high, low, close, length)

    def bb(
        self,
        source: Series[Decimal],
        length: int = 20,
        mult: Decimal = Decimal("2"),
    ) -> tuple[Decimal, Decimal, Decimal]:
        return ta.bb(source, length, mult)

    def change(self, source: Series[Decimal], length: int = 1) -> Decimal:
        return ta.change(source, length)

    def stdev(self, source: Series[Decimal], length: int) -> Decimal:
        return ta.stdev(source, length)

    def rma(self, source: Series[Decimal], length: int) -> Decimal:
        return ta.rma(source, length)

    def tr(
        self,
        high: Series[Decimal],
        low: Series[Decimal],
        close: Series[Decimal],
    ) -> Decimal:
        return ta.tr(high, low, close)

    # Faz 1
    def smma(self, source: Series[Decimal], length: int) -> Decimal:
        return ta.smma(source, length)

    def cross(self, s1: Series[Decimal], s2: Series[Decimal]) -> bool:
        return ta.cross(s1, s2)

    def mom(self, source: Series[Decimal], length: int = 10) -> Decimal:
        return ta.mom(source, length)

    def roc(self, source: Series[Decimal], length: int = 10) -> Decimal:
        return ta.roc(source, length)

    # Faz 2
    def wma(self, source: Series[Decimal], length: int) -> Decimal:
        return ta.wma(source, length)

    def hma(self, source: Series[Decimal], length: int) -> Decimal:
        return ta.hma(source, length)

    def vwma(self, source: Series[Decimal], volume: Series[Decimal], length: int) -> Decimal:
        return ta.vwma(source, volume, length)

    # Faz 3
    def stoch(
        self,
        source: Series[Decimal],
        high: Series[Decimal],
        low: Series[Decimal],
        length: int,
    ) -> Decimal:
        return ta.stoch(source, high, low, length)

    def pivothigh(self, source: Series[Decimal], leftbars: int, rightbars: int):
        return ta.pivothigh(source, leftbars, rightbars)

    def pivotlow(self, source: Series[Decimal], leftbars: int, rightbars: int):
        return ta.pivotlow(source, leftbars, rightbars)

    # Faz 4
    def dmi(
        self,
        high: Series[Decimal],
        low: Series[Decimal],
        close: Series[Decimal],
        di_length: int = 14,
        adx_smoothing: int = 14,
    ) -> tuple[Decimal, Decimal, Decimal]:
        return ta.dmi(high, low, close, di_length, adx_smoothing)

    def linreg(self, source: Series[Decimal], length: int, offset: int = 0) -> Decimal:
        return ta.linreg(source, length, offset)

    # Faz 5
    def cci(self, source: Series[Decimal], length: int = 20) -> Decimal:
        return ta.cci(source, length)

    def mfi(
        self,
        high: Series[Decimal],
        low: Series[Decimal],
        close: Series[Decimal],
        volume: Series[Decimal],
        length: int = 14,
    ) -> Decimal:
        return ta.mfi(high, low, close, volume, length)

    def wpr(
        self,
        high: Series[Decimal],
        low: Series[Decimal],
        close: Series[Decimal],
        length: int = 14,
    ) -> Decimal:
        return ta.wpr(high, low, close, length)

    def obv(self, close: Series[Decimal], volume: Series[Decimal]) -> Decimal:
        return ta.obv(close, volume)

    def vwap(
        self,
        high: Series[Decimal],
        low: Series[Decimal],
        close: Series[Decimal],
        volume: Series[Decimal],
    ) -> Decimal:
        return ta.vwap(high, low, close, volume)

    def cum(self, source: Series[Decimal]) -> Decimal:
        return ta.cum(source)

    # Faz 6
    def kc(
        self,
        source: Series[Decimal],
        length: int,
        mult: Decimal,
        atr_length: int,
        high: Series[Decimal] = None,
        low: Series[Decimal] = None,
        close: Series[Decimal] = None,
    ) -> tuple[Decimal, Decimal, Decimal]:
        return ta.kc(source, length, mult, atr_length, high, low, close)

    def supertrend(
        self,
        high: Series[Decimal],
        low: Series[Decimal],
        close: Series[Decimal],
        factor: Decimal = Decimal("3"),
        atr_period: int = 10,
    ) -> tuple[Decimal, int]:
        return ta.supertrend(high, low, close, factor, atr_period)

    def sar(
        self,
        high: Series[Decimal],
        low: Series[Decimal],
        start: Decimal = Decimal("0.02"),
        inc: Decimal = Decimal("0.02"),
        max_val: Decimal = Decimal("0.2"),
    ) -> Decimal:
        return ta.sar(high, low, start, inc, max_val)

    # Faz 7
    def rising(self, source: Series[Decimal], length: int) -> bool:
        return ta.rising(source, length)

    def falling(self, source: Series[Decimal], length: int) -> bool:
        return ta.falling(source, length)

    def variance(self, source: Series[Decimal], length: int) -> Decimal:
        return ta.variance(source, length)

    def median(self, source: Series[Decimal], length: int) -> Decimal:
        return ta.median(source, length)

    def correlation(
        self, source1: Series[Decimal], source2: Series[Decimal], length: int
    ) -> Decimal:
        return ta.correlation(source1, source2, length)

    def highestbars(self, source: Series[Decimal], length: int) -> int:
        return ta.highestbars(source, length)

    def lowestbars(self, source: Series[Decimal], length: int) -> int:
        return ta.lowestbars(source, length)

    def bbw(
        self, source: Series[Decimal], length: int = 20, mult: Decimal = Decimal("2")
    ) -> Decimal:
        return ta.bbw(source, length, mult)

    def kcw(
        self,
        source: Series[Decimal],
        length: int,
        mult: Decimal,
        atr_length: int,
        high: Series[Decimal] = None,
        low: Series[Decimal] = None,
        close: Series[Decimal] = None,
    ) -> Decimal:
        return ta.kcw(source, length, mult, atr_length, high, low, close)

    def barsince(self, condition: Series[bool]) -> int:
        return ta.barsince(condition)

    def valuewhen(
        self, condition: Series[bool], source: Series[Decimal], occurrence: int = 0
    ) -> Decimal:
        return ta.valuewhen(condition, source, occurrence)


class MathNamespace:
    """Namespace for math.* functions."""

    def abs(self, x: Decimal) -> Decimal:
        return math_funcs.abs_val(x)

    def max(self, a: Decimal, b: Decimal) -> Decimal:
        return math_funcs.max_val(a, b)

    def min(self, a: Decimal, b: Decimal) -> Decimal:
        return math_funcs.min_val(a, b)

    def round(self, x: Decimal, precision: int = 0) -> Decimal:
        return math_funcs.round_val(x, precision)

    def ceil(self, x: Decimal) -> Decimal:
        return math_funcs.ceil(x)

    def floor(self, x: Decimal) -> Decimal:
        return math_funcs.floor(x)

    def sign(self, x: Decimal) -> int:
        return math_funcs.sign(x)

    def pow(self, base: Decimal, exp: Decimal) -> Decimal:
        return math_funcs.pow_val(base, exp)

    def sqrt(self, x: Decimal) -> Decimal:
        return math_funcs.sqrt(x)

    def log(self, x: Decimal) -> Decimal:
        return math_funcs.log(x)

    def exp(self, x: Decimal) -> Decimal:
        return math_funcs.exp(x)
