"""Tests for genetic algorithm optimization."""

from decimal import Decimal

import pytest

from finsaas.core.context import BarContext
from finsaas.core.types import Side, SymbolInfo, Timeframe
from finsaas.data.feed import InMemoryFeed
from finsaas.engine.runner import BacktestConfig
from finsaas.optimization.genetic import GeneticOptimizer
from finsaas.optimization.objective import SharpeObjective
from finsaas.optimization.space import ParameterSpace
from finsaas.strategy.base import Strategy
from finsaas.strategy.parameters import IntParam


class GeneticTestStrategy(Strategy):
    fast = IntParam(default=3, min_val=2, max_val=5, step=1)
    slow = IntParam(default=7, min_val=5, max_val=10, step=1)

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


class TestGeneticOptimizer:
    def test_genetic_runs(self, sample_bars, symbol_info):
        feed = InMemoryFeed(sample_bars, symbol="TEST", timeframe="1h")
        config = BacktestConfig(
            symbol_info=symbol_info,
            timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
        )
        space = ParameterSpace.from_strategy(GeneticTestStrategy)
        objective = SharpeObjective()

        optimizer = GeneticOptimizer(
            strategy_cls=GeneticTestStrategy,
            feed=feed,
            config=config,
            objective=objective,
            space=space,
            population_size=5,
            generations=3,
            seed=42,
        )
        result = optimizer.run()

        assert result.total_trials > 0
        assert result.best_params is not None
        assert "fast" in result.best_params
        assert "slow" in result.best_params
        assert result.method == "genetic"

    def test_genetic_deterministic_with_seed(self, sample_bars, symbol_info):
        """Same seed should produce same results."""
        feed = InMemoryFeed(sample_bars, symbol="TEST", timeframe="1h")
        config = BacktestConfig(
            symbol_info=symbol_info,
            timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
        )
        space = ParameterSpace.from_strategy(GeneticTestStrategy)
        objective = SharpeObjective()

        results = []
        for _ in range(2):
            optimizer = GeneticOptimizer(
                strategy_cls=GeneticTestStrategy,
                feed=feed,
                config=config,
                objective=objective,
                space=space,
                population_size=5,
                generations=3,
                seed=42,
            )
            results.append(optimizer.run())

        assert results[0].best_params == results[1].best_params
        assert results[0].best_value == results[1].best_value
