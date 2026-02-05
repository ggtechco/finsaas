"""Tests for the Strategy DSL."""

from decimal import Decimal

import pytest

from finsaas.core.context import BarContext
from finsaas.core.types import Side, SymbolInfo, Timeframe
from finsaas.data.feed import InMemoryFeed
from finsaas.engine.commission import ZeroCommission
from finsaas.engine.loop import EventLoop
from finsaas.engine.slippage import ZeroSlippage
from finsaas.strategy.base import Strategy
from finsaas.strategy.parameters import IntParam, FloatParam, EnumParam, BoolParam
from finsaas.strategy.registry import get_strategy, list_strategies


class TestStrategyParameters:
    def test_int_param_default(self):
        class TestStrat(Strategy):
            length = IntParam(default=14, min_val=1, max_val=100)

            def on_bar(self, ctx: BarContext) -> None:
                pass

        s = TestStrat()
        assert s.length == 14

    def test_int_param_set(self):
        class TestStrat2(Strategy):
            length = IntParam(default=14, min_val=1, max_val=100)

            def on_bar(self, ctx: BarContext) -> None:
                pass

        s = TestStrat2()
        s.length = 20
        assert s.length == 20

    def test_int_param_validation(self):
        class TestStrat3(Strategy):
            length = IntParam(default=14, min_val=1, max_val=100)

            def on_bar(self, ctx: BarContext) -> None:
                pass

        s = TestStrat3()
        with pytest.raises(ValueError):
            s.length = 200  # Exceeds max

    def test_float_param(self):
        class TestStrat4(Strategy):
            threshold = FloatParam(default=0.5, min_val=0.0, max_val=1.0)

            def on_bar(self, ctx: BarContext) -> None:
                pass

        s = TestStrat4()
        assert s.threshold == Decimal("0.5")

    def test_enum_param(self):
        class TestStrat5(Strategy):
            mode = EnumParam(default="fast", choices=["fast", "slow", "auto"])

            def on_bar(self, ctx: BarContext) -> None:
                pass

        s = TestStrat5()
        assert s.mode == "fast"
        s.mode = "slow"
        assert s.mode == "slow"

        with pytest.raises(ValueError):
            s.mode = "invalid"

    def test_bool_param(self):
        class TestStrat6(Strategy):
            use_filter = BoolParam(default=True)

            def on_bar(self, ctx: BarContext) -> None:
                pass

        s = TestStrat6()
        assert s.use_filter is True

    def test_get_set_parameters(self):
        class TestStrat7(Strategy):
            fast = IntParam(default=10)
            slow = IntParam(default=20)

            def on_bar(self, ctx: BarContext) -> None:
                pass

        s = TestStrat7()
        params = s.get_parameters()
        assert params == {"fast": 10, "slow": 20}

        s.set_parameters({"fast": 15, "slow": 30})
        assert s.fast == 15
        assert s.slow == 30


class TestStrategyRegistry:
    def test_auto_registration(self):
        strategies = list_strategies()
        # All test strategies above should be registered
        assert len(strategies) > 0

    def test_get_strategy(self):
        class RegisteredStrat(Strategy):
            def on_bar(self, ctx: BarContext) -> None:
                pass

        cls = get_strategy("RegisteredStrat")
        assert cls is RegisteredStrat


class TestStrategyExecution:
    def test_strategy_with_sma(self, sample_bars, symbol_info):
        class SMACross(Strategy):
            fast_len = IntParam(default=3)
            slow_len = IntParam(default=5)

            def on_init(self):
                self.fast_ma = self.create_series("fast")
                self.slow_ma = self.create_series("slow")

            def on_bar(self, ctx: BarContext) -> None:
                self.fast_ma.current = self.ta.sma(self.close, self.fast_len)
                self.slow_ma.current = self.ta.sma(self.close, self.slow_len)

                if self.ta.crossover(self.fast_ma, self.slow_ma):
                    self.entry("long", Side.LONG)
                elif self.ta.crossunder(self.fast_ma, self.slow_ma):
                    self.close_position("long")

        feed = InMemoryFeed(sample_bars, symbol="TEST", timeframe="1h")
        loop = EventLoop(
            feed=feed, symbol_info=symbol_info, timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
            commission_model=ZeroCommission(), slippage_model=ZeroSlippage(),
        )
        strategy = SMACross()
        loop.run(strategy)

        # Should complete without errors
        assert len(loop.portfolio.equity_curve) == len(sample_bars)
