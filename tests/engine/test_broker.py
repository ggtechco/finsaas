"""Tests for SimulatedBroker."""

from datetime import datetime
from decimal import Decimal

import pytest

from finsaas.core.types import OHLCV, OrderAction, OrderType, Side
from finsaas.engine.broker import SimulatedBroker
from finsaas.engine.commission import PercentageCommission, ZeroCommission
from finsaas.engine.order import Order
from finsaas.engine.slippage import ZeroSlippage


@pytest.fixture
def broker() -> SimulatedBroker:
    return SimulatedBroker(
        commission_model=ZeroCommission(),
        slippage_model=ZeroSlippage(),
    )


@pytest.fixture
def sample_bar() -> OHLCV:
    return OHLCV(
        timestamp=datetime(2023, 1, 1, 1, 0, 0),
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("95"),
        close=Decimal("105"),
        volume=Decimal("1000"),
    )


class TestMarketOrders:
    def test_market_buy_fills_at_open(self, broker: SimulatedBroker, sample_bar: OHLCV):
        order = Order(
            action=OrderAction.ENTRY,
            side=Side.LONG,
            order_type=OrderType.MARKET,
            quantity=Decimal("10"),
            tag="test",
        )
        broker.submit_order(order)
        fills = broker.process_bar(sample_bar, 0)

        assert len(fills) == 1
        assert fills[0].price == Decimal("100")  # Opens at bar's open
        assert fills[0].quantity == Decimal("10")
        assert fills[0].side == Side.LONG

    def test_market_sell_fills_at_open(self, broker: SimulatedBroker, sample_bar: OHLCV):
        order = Order(
            action=OrderAction.ENTRY,
            side=Side.SHORT,
            order_type=OrderType.MARKET,
            quantity=Decimal("5"),
        )
        broker.submit_order(order)
        fills = broker.process_bar(sample_bar, 0)

        assert len(fills) == 1
        assert fills[0].price == Decimal("100")

    def test_pending_orders_cleared_after_fill(self, broker: SimulatedBroker, sample_bar: OHLCV):
        order = Order(
            action=OrderAction.ENTRY,
            side=Side.LONG,
            order_type=OrderType.MARKET,
            quantity=Decimal("1"),
        )
        broker.submit_order(order)
        assert len(broker.pending_orders) == 1

        broker.process_bar(sample_bar, 0)
        assert len(broker.pending_orders) == 0


class TestLimitOrders:
    def test_limit_buy_fills_when_low_reaches(self, broker: SimulatedBroker, sample_bar: OHLCV):
        """Limit buy at 96 should fill when bar low is 95."""
        order = Order(
            action=OrderAction.ENTRY,
            side=Side.LONG,
            order_type=OrderType.LIMIT,
            quantity=Decimal("10"),
            limit_price=Decimal("96"),
        )
        broker.submit_order(order)
        fills = broker.process_bar(sample_bar, 0)

        assert len(fills) == 1
        assert fills[0].price == Decimal("96")

    def test_limit_buy_no_fill_when_price_above(self, broker: SimulatedBroker):
        """Limit buy at 85 should NOT fill when bar low is 95."""
        bar = OHLCV(
            timestamp=datetime(2023, 1, 1),
            open=Decimal("100"), high=Decimal("110"),
            low=Decimal("95"), close=Decimal("105"), volume=Decimal("1000"),
        )
        order = Order(
            action=OrderAction.ENTRY,
            side=Side.LONG,
            order_type=OrderType.LIMIT,
            quantity=Decimal("10"),
            limit_price=Decimal("85"),
        )
        broker.submit_order(order)
        fills = broker.process_bar(bar, 0)

        assert len(fills) == 0
        assert len(broker.pending_orders) == 1


class TestStopOrders:
    def test_stop_buy_fills_when_high_reaches(self, broker: SimulatedBroker, sample_bar: OHLCV):
        """Stop buy at 108 should fill when bar high is 110."""
        order = Order(
            action=OrderAction.ENTRY,
            side=Side.LONG,
            order_type=OrderType.STOP,
            quantity=Decimal("10"),
            stop_price=Decimal("108"),
        )
        broker.submit_order(order)
        fills = broker.process_bar(sample_bar, 0)

        assert len(fills) == 1
        # Fill at max(open, stop_price) = max(100, 108) = 108
        assert fills[0].price == Decimal("108")


class TestOrderCancellation:
    def test_cancel_all(self, broker: SimulatedBroker):
        for i in range(3):
            broker.submit_order(Order(
                action=OrderAction.ENTRY,
                side=Side.LONG,
                order_type=OrderType.MARKET,
                quantity=Decimal("1"),
            ))
        assert len(broker.pending_orders) == 3
        cancelled = broker.cancel_all()
        assert cancelled == 3
        assert len(broker.pending_orders) == 0

    def test_cancel_by_tag(self, broker: SimulatedBroker):
        broker.submit_order(Order(
            action=OrderAction.ENTRY, side=Side.LONG,
            order_type=OrderType.MARKET, quantity=Decimal("1"), tag="a",
        ))
        broker.submit_order(Order(
            action=OrderAction.ENTRY, side=Side.LONG,
            order_type=OrderType.MARKET, quantity=Decimal("1"), tag="b",
        ))
        cancelled = broker.cancel_all(tag="a")
        assert cancelled == 1
        assert len(broker.pending_orders) == 1


class TestCommission:
    def test_commission_applied(self, sample_bar: OHLCV):
        broker = SimulatedBroker(
            commission_model=PercentageCommission(Decimal("0.001")),
            slippage_model=ZeroSlippage(),
        )
        order = Order(
            action=OrderAction.ENTRY,
            side=Side.LONG,
            order_type=OrderType.MARKET,
            quantity=Decimal("10"),
        )
        broker.submit_order(order)
        fills = broker.process_bar(sample_bar, 0)

        assert len(fills) == 1
        # Commission = 100 * 10 * 0.001 = 1.0
        assert fills[0].commission == Decimal("1.000")
