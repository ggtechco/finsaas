"""Tests for EventLoop - the core simulation engine."""

from datetime import datetime
from decimal import Decimal

import pytest

from finsaas.core.context import BarContext
from finsaas.core.types import OHLCV, Side, SymbolInfo, Timeframe
from finsaas.data.feed import InMemoryFeed
from finsaas.engine.commission import ZeroCommission
from finsaas.engine.loop import EventLoop
from finsaas.engine.slippage import ZeroSlippage
from finsaas.strategy.base import Strategy
from finsaas.strategy.parameters import IntParam


class SimpleStrategy(Strategy):
    """Buy on bar 2, sell on bar 5."""

    def on_bar(self, ctx: BarContext) -> None:
        if ctx.bar_index == 2:
            self.entry("test", Side.LONG, qty=Decimal("10"))
        elif ctx.bar_index == 5:
            self.close_position("test")


class TestEventLoop:
    def test_runs_all_bars(self, sample_bars, symbol_info):
        feed = InMemoryFeed(sample_bars, symbol="TEST", timeframe="1h")
        loop = EventLoop(
            feed=feed,
            symbol_info=symbol_info,
            timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
            commission_model=ZeroCommission(),
            slippage_model=ZeroSlippage(),
        )

        strategy = SimpleStrategy()
        loop.run(strategy)

        # Should have equity points for all bars
        assert len(loop.portfolio.equity_curve) == len(sample_bars)

    def test_order_fills_next_bar(self, sample_bars, symbol_info):
        """Orders from bar N should fill at bar N+1's open."""
        feed = InMemoryFeed(sample_bars, symbol="TEST", timeframe="1h")
        loop = EventLoop(
            feed=feed,
            symbol_info=symbol_info,
            timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
            commission_model=ZeroCommission(),
            slippage_model=ZeroSlippage(),
        )

        strategy = SimpleStrategy()
        loop.run(strategy)

        trades = loop.portfolio.trade_results
        # Strategy enters on bar 2, order fills on bar 3's open
        # sample_bars[3].open = 105
        assert len(trades) >= 1
        assert trades[0].entry_price == sample_bars[3].open

    def test_positions_closed_at_end(self, symbol_info):
        """All positions should be closed at end of backtest."""
        bars = [
            OHLCV(datetime(2023, 1, 1, i), Decimal("100"), Decimal("105"),
                   Decimal("95"), Decimal("100"), Decimal("1000"))
            for i in range(5)
        ]
        feed = InMemoryFeed(bars, symbol="TEST", timeframe="1h")

        class AlwaysBuyStrategy(Strategy):
            def on_bar(self, ctx: BarContext) -> None:
                if ctx.bar_index == 0:
                    self.entry("long", Side.LONG, qty=Decimal("1"))

        loop = EventLoop(
            feed=feed, symbol_info=symbol_info, timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
            commission_model=ZeroCommission(), slippage_model=ZeroSlippage(),
        )
        strategy = AlwaysBuyStrategy()
        loop.run(strategy)

        # Position should be closed by end
        assert loop.portfolio.open_position_count == 0

    def test_context_series_updated(self, sample_bars, symbol_info):
        """Bar context OHLCV series should be populated."""
        feed = InMemoryFeed(sample_bars, symbol="TEST", timeframe="1h")

        class CheckContextStrategy(Strategy):
            def __init__(self):
                super().__init__()
                self.observed_closes: list[Decimal] = []

            def on_bar(self, ctx: BarContext) -> None:
                self.observed_closes.append(ctx.close.current)

        loop = EventLoop(
            feed=feed, symbol_info=symbol_info, timeframe=Timeframe.H1,
            initial_capital=Decimal("10000"),
            commission_model=ZeroCommission(), slippage_model=ZeroSlippage(),
        )
        strategy = CheckContextStrategy()
        loop.run(strategy)

        assert len(strategy.observed_closes) == len(sample_bars)
        assert strategy.observed_closes[0] == sample_bars[0].close
