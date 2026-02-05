"""Determinism tests - verify backtests produce identical results."""

from decimal import Decimal

import pytest

from finsaas.core.context import BarContext
from finsaas.core.types import Side, SymbolInfo, Timeframe
from finsaas.data.feed import InMemoryFeed
from finsaas.engine.commission import PercentageCommission
from finsaas.engine.runner import BacktestConfig, BacktestRunner
from finsaas.engine.slippage import PercentageSlippage
from finsaas.strategy.base import Strategy
from finsaas.strategy.parameters import IntParam


class DeterminismTestStrategy(Strategy):
    fast = IntParam(default=3)
    slow = IntParam(default=5)

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


class TestDeterminism:
    def test_backtest_deterministic_10_runs(self, sample_bars, symbol_info):
        """Run the same backtest 10 times and verify identical results."""
        feed = InMemoryFeed(sample_bars, symbol="TEST", timeframe="1h")
        config = BacktestConfig(
            symbol_info=symbol_info,
            timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
            commission_model=PercentageCommission(Decimal("0.001")),
            slippage_model=PercentageSlippage(Decimal("0.0005")),
        )

        results = []
        for _ in range(10):
            strategy = DeterminismTestStrategy()
            runner = BacktestRunner(feed, config)
            result = runner.run(strategy)
            results.append(result)

        # All results should have the same hash
        hashes = {r.run_hash for r in results}
        assert len(hashes) == 1, f"Expected 1 unique hash, got {len(hashes)}"

        # All results should have identical final equity
        equities = {r.final_equity for r in results}
        assert len(equities) == 1, f"Expected 1 unique equity, got {len(equities)}"

        # All results should have identical trade counts
        trade_counts = {len(r.trades) for r in results}
        assert len(trade_counts) == 1

        # All trade P&L values should match
        if results[0].trades:
            for i, trade in enumerate(results[0].trades):
                for result in results[1:]:
                    assert trade.pnl == result.trades[i].pnl, (
                        f"Trade {i} P&L mismatch: {trade.pnl} != {result.trades[i].pnl}"
                    )

    def test_same_hash_same_result(self, sample_bars, symbol_info):
        """Verify the deterministic hash matches between runs."""
        feed = InMemoryFeed(sample_bars, symbol="TEST", timeframe="1h")
        config = BacktestConfig(
            symbol_info=symbol_info,
            timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
        )

        s1 = DeterminismTestStrategy()
        s2 = DeterminismTestStrategy()

        r1 = BacktestRunner(feed, config).run(s1)
        r2 = BacktestRunner(feed, config).run(s2)

        assert r1.run_hash == r2.run_hash
        assert r1.final_equity == r2.final_equity
