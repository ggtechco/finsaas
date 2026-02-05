"""Performance benchmark script.

Measures backtest execution time for varying bar counts.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finsaas.core.context import BarContext
from finsaas.core.types import OHLCV, Side, SymbolInfo, Timeframe
from finsaas.data.feed import InMemoryFeed
from finsaas.engine.commission import PercentageCommission
from finsaas.engine.runner import BacktestConfig, BacktestRunner
from finsaas.engine.slippage import PercentageSlippage
from finsaas.strategy.base import Strategy
from finsaas.strategy.parameters import IntParam


class BenchmarkStrategy(Strategy):
    fast = IntParam(default=10)
    slow = IntParam(default=30)

    def on_init(self):
        self.fast_ma = self.create_series("fast")
        self.slow_ma = self.create_series("slow")

    def on_bar(self, ctx: BarContext) -> None:
        self.fast_ma.current = self.ta.sma(self.close, self.fast)
        self.slow_ma.current = self.ta.sma(self.close, self.slow)

        if self.ta.crossover(self.fast_ma, self.slow_ma):
            self.entry("long", Side.LONG)
        elif self.ta.crossunder(self.fast_ma, self.slow_ma):
            self.close_position("long")


def generate_bars(count: int) -> list[OHLCV]:
    """Generate synthetic OHLCV bars."""
    import random

    random.seed(42)
    bars: list[OHLCV] = []
    price = Decimal("100")

    for i in range(count):
        change = Decimal(str(random.uniform(-2, 2)))
        open_p = price
        close_p = price + change
        high_p = max(open_p, close_p) + Decimal(str(random.uniform(0, 1)))
        low_p = min(open_p, close_p) - Decimal(str(random.uniform(0, 1)))
        volume = Decimal(str(random.randint(100, 10000)))

        bars.append(OHLCV(
            timestamp=datetime(2023, 1, 1, i % 24, 0, 0),
            open=open_p, high=high_p, low=low_p, close=close_p, volume=volume,
        ))
        price = close_p

    return bars


def main() -> None:
    print("FinSaaS Performance Benchmark")
    print("=" * 50)

    bar_counts = [100, 1_000, 10_000, 50_000, 100_000]

    for count in bar_counts:
        bars = generate_bars(count)
        feed = InMemoryFeed(bars, symbol="BENCH", timeframe="1h")
        config = BacktestConfig(
            symbol_info=SymbolInfo(ticker="BENCH"),
            timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
            commission_model=PercentageCommission(Decimal("0.001")),
            slippage_model=PercentageSlippage(Decimal("0.0005")),
        )

        strategy = BenchmarkStrategy()
        runner = BacktestRunner(feed, config)

        start = time.perf_counter()
        result = runner.run(strategy)
        elapsed = time.perf_counter() - start

        bars_per_sec = count / elapsed if elapsed > 0 else float("inf")
        print(
            f"  {count:>8,} bars: {elapsed:>8.3f}s "
            f"({bars_per_sec:>10,.0f} bars/sec) "
            f"| Trades: {len(result.trades)}"
        )

    print("=" * 50)


if __name__ == "__main__":
    main()
