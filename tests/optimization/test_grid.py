"""Tests for grid search optimization."""

from decimal import Decimal

import pytest

from finsaas.core.context import BarContext
from finsaas.core.types import Side, SymbolInfo, Timeframe
from finsaas.data.feed import InMemoryFeed
from finsaas.engine.runner import BacktestConfig
from finsaas.optimization.grid import GridSearchOptimizer
from finsaas.optimization.objective import SharpeObjective
from finsaas.optimization.space import ParameterSpace
from finsaas.strategy.base import Strategy
from finsaas.strategy.parameters import IntParam


class OptTestStrategy(Strategy):
    fast = IntParam(default=3, min_val=2, max_val=4, step=1)
    slow = IntParam(default=5, min_val=4, max_val=6, step=1)

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


class TestGridSearch:
    def test_parameter_space_extraction(self):
        space = ParameterSpace.from_strategy(OptTestStrategy)
        assert len(space.ranges) == 2
        assert space.dimension_names == ["fast", "slow"]
        # fast: [2,3,4] = 3 values, slow: [4,5,6] = 3 values
        assert space.total_combinations == 9

    def test_grid_search_runs(self, sample_bars, symbol_info):
        feed = InMemoryFeed(sample_bars, symbol="TEST", timeframe="1h")
        config = BacktestConfig(
            symbol_info=symbol_info,
            timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
        )
        space = ParameterSpace.from_strategy(OptTestStrategy)
        objective = SharpeObjective()

        optimizer = GridSearchOptimizer(
            strategy_cls=OptTestStrategy,
            feed=feed,
            config=config,
            objective=objective,
            space=space,
        )
        result = optimizer.run()

        assert result.total_trials == 9
        assert result.best_params is not None
        assert "fast" in result.best_params
        assert "slow" in result.best_params

    def test_grid_iter(self):
        space = ParameterSpace.from_strategy(OptTestStrategy)
        combos = list(space.grid_iter())
        assert len(combos) == 9
        # First combo should be fast=2, slow=4
        assert combos[0] == {"fast": 2, "slow": 4}
