"""Tests for Portfolio."""

from datetime import datetime
from decimal import Decimal

import pytest

from finsaas.core.types import OHLCV, OrderAction, Side
from finsaas.engine.order import Fill
from finsaas.engine.portfolio import Portfolio


@pytest.fixture
def portfolio() -> Portfolio:
    return Portfolio(initial_capital=Decimal("10000"))


class TestPortfolioBasic:
    def test_initial_state(self, portfolio: Portfolio):
        assert portfolio.cash == Decimal("10000")
        assert portfolio.initial_capital == Decimal("10000")
        assert portfolio.open_position_count == 0
        assert len(portfolio.trade_results) == 0

    def test_open_long_position(self, portfolio: Portfolio):
        fill = Fill(
            order_id="test1",
            side=Side.LONG,
            price=Decimal("100"),
            quantity=Decimal("10"),
            commission=Decimal("1"),
            slippage=Decimal("0"),
            timestamp=datetime(2023, 1, 1),
            tag="long_entry",
        )
        portfolio.process_fill(fill, OrderAction.ENTRY, bar_index=0)

        assert portfolio.open_position_count == 1
        assert portfolio.has_position("long_entry")
        # Cash = 10000 - (100*10) - 1 = 8999
        assert portfolio.cash == Decimal("8999")

    def test_close_long_position(self, portfolio: Portfolio):
        # Open
        entry_fill = Fill(
            order_id="e1", side=Side.LONG, price=Decimal("100"),
            quantity=Decimal("10"), commission=Decimal("1"),
            slippage=Decimal("0"), timestamp=datetime(2023, 1, 1),
            tag="pos1",
        )
        portfolio.process_fill(entry_fill, OrderAction.ENTRY, bar_index=0)

        # Close
        exit_fill = Fill(
            order_id="x1", side=Side.LONG, price=Decimal("110"),
            quantity=Decimal("10"), commission=Decimal("1"),
            slippage=Decimal("0"), timestamp=datetime(2023, 1, 2),
            tag="pos1",
        )
        portfolio.process_fill(exit_fill, OrderAction.CLOSE, bar_index=1)

        assert portfolio.open_position_count == 0
        assert len(portfolio.trade_results) == 1
        # P&L = (110-100)*10 - 1 - 1 = 98
        assert portfolio.trade_results[0].pnl == Decimal("98")

    def test_equity_calculation(self, portfolio: Portfolio):
        fill = Fill(
            order_id="e1", side=Side.LONG, price=Decimal("100"),
            quantity=Decimal("10"), commission=Decimal("0"),
            slippage=Decimal("0"), timestamp=datetime(2023, 1, 1),
            tag="test",
        )
        portfolio.process_fill(fill, OrderAction.ENTRY, bar_index=0)

        # Equity at price 110: cash (9000) + position (10*110) = 10100
        equity = portfolio.equity(Decimal("110"))
        assert equity == Decimal("10100")

    def test_record_equity(self, portfolio: Portfolio):
        bar = OHLCV(
            timestamp=datetime(2023, 1, 1),
            open=Decimal("100"), high=Decimal("105"),
            low=Decimal("98"), close=Decimal("103"),
            volume=Decimal("1000"),
        )
        point = portfolio.record_equity(bar, 0)
        assert point.equity == Decimal("10000")
        assert point.drawdown == Decimal("0")

    def test_close_all_positions(self, portfolio: Portfolio):
        for i, tag in enumerate(["a", "b", "c"]):
            fill = Fill(
                order_id=f"e{i}", side=Side.LONG, price=Decimal("100"),
                quantity=Decimal("1"), commission=Decimal("0"),
                slippage=Decimal("0"), timestamp=datetime(2023, 1, 1),
                tag=tag,
            )
            portfolio.process_fill(fill, OrderAction.ENTRY, bar_index=0)

        assert portfolio.open_position_count == 3
        portfolio.close_all_positions(
            Decimal("110"), datetime(2023, 1, 2), 1
        )
        assert portfolio.open_position_count == 0
        assert len(portfolio.trade_results) == 3
