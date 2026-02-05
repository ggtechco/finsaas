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
