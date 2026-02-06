"""Built-in example strategies for dashboard testing."""

from __future__ import annotations

from finsaas.core.context import BarContext
from finsaas.core.types import Side
from finsaas.strategy.base import Strategy
from finsaas.strategy.parameters import FloatParam, IntParam


class SMACrossover(Strategy):
    """Simple Moving Average crossover strategy.

    Goes long when fast SMA crosses above slow SMA,
    closes when fast SMA crosses below slow SMA.
    """

    fast_length = IntParam(default=10, min_val=2, max_val=100, step=5, description="Fast SMA period")
    slow_length = IntParam(default=20, min_val=5, max_val=200, step=10, description="Slow SMA period")

    def on_init(self) -> None:
        self.fast_ma = self.create_series("fast_ma")
        self.slow_ma = self.create_series("slow_ma")

    def on_bar(self, ctx: BarContext) -> None:
        self.fast_ma.current = self.ta.sma(self.close, self.fast_length)
        self.slow_ma.current = self.ta.sma(self.close, self.slow_length)

        if self.ta.crossover(self.fast_ma, self.slow_ma):
            self.entry("sma_cross", Side.LONG)
        elif self.ta.crossunder(self.fast_ma, self.slow_ma):
            self.close_position("sma_cross")


class RSIMeanReversion(Strategy):
    """RSI mean-reversion strategy.

    Goes long when RSI drops below oversold level,
    closes when RSI rises above overbought level.
    """

    rsi_length = IntParam(default=14, min_val=2, max_val=50, step=2, description="RSI period")
    oversold = FloatParam(default=30.0, min_val=10.0, max_val=50.0, step=5.0, description="Oversold level")
    overbought = FloatParam(default=70.0, min_val=50.0, max_val=90.0, step=5.0, description="Overbought level")

    def on_bar(self, ctx: BarContext) -> None:
        rsi_val = self.ta.rsi(self.close, self.rsi_length)

        if rsi_val < self.oversold:
            self.entry("rsi_mr", Side.LONG)
        elif rsi_val > self.overbought:
            self.close_position("rsi_mr")
