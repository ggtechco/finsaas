"""Simulated broker for order matching and execution.

Implements the order execution model described in the architecture:
- Orders submitted on bar N are executed on bar N+1
- MARKET orders fill at N+1's open (with slippage)
- LIMIT/STOP orders check against N+1's OHLC range
- No look-ahead bias
"""

from __future__ import annotations

import structlog
from decimal import Decimal

from finsaas.core.events import FillEvent
from finsaas.core.types import OHLCV, OrderAction, OrderStatus, OrderType, Side
from finsaas.engine.commission import CommissionModel, PercentageCommission
from finsaas.engine.order import Fill, Order
from finsaas.engine.slippage import PercentageSlippage, SlippageModel

logger = structlog.get_logger()


class SimulatedBroker:
    """Simulated broker that matches orders against OHLCV bar data.

    Order execution rules (no look-ahead bias):
    - MARKET: fills at bar's open price (with slippage)
    - LIMIT BUY: fills if bar's low <= limit_price, at limit_price
    - LIMIT SELL: fills if bar's high >= limit_price, at limit_price
    - STOP BUY: fills if bar's high >= stop_price, at stop_price (with slippage)
    - STOP SELL: fills if bar's low <= stop_price, at stop_price (with slippage)
    """

    def __init__(
        self,
        commission_model: CommissionModel | None = None,
        slippage_model: SlippageModel | None = None,
    ) -> None:
        self._commission = commission_model or PercentageCommission()
        self._slippage = slippage_model or PercentageSlippage()
        self._pending_orders: list[Order] = []

    @property
    def pending_orders(self) -> list[Order]:
        return list(self._pending_orders)

    def submit_order(self, order: Order) -> None:
        """Submit a new order to the broker queue."""
        self._pending_orders.append(order)
        logger.debug("order_submitted", order_id=order.id, side=order.side.value,
                     type=order.order_type.value, qty=str(order.quantity))

    def cancel_all(self, tag: str | None = None) -> int:
        """Cancel all pending orders, optionally filtered by tag."""
        cancelled = 0
        remaining: list[Order] = []
        for order in self._pending_orders:
            if tag is None or order.tag == tag:
                order.cancel()
                cancelled += 1
            else:
                remaining.append(order)
        self._pending_orders = remaining
        return cancelled

    def process_bar(self, bar: OHLCV, bar_index: int) -> list[Fill]:
        """Process all pending orders against the given bar.

        This is called at the START of each bar, BEFORE strategy.on_bar().
        Orders from the previous bar get matched against this bar's data.

        Returns a list of fills.
        """
        fills: list[Fill] = []
        remaining: list[Order] = []

        for order in self._pending_orders:
            fill = self._try_fill(order, bar, bar_index)
            if fill is not None:
                fills.append(fill)
                order.status = OrderStatus.FILLED
                order.filled_at = bar.timestamp
                order.fill_price = fill.price
                order.commission = fill.commission
                order.slippage = fill.slippage
            else:
                remaining.append(order)

        self._pending_orders = remaining
        return fills

    def _try_fill(self, order: Order, bar: OHLCV, bar_index: int) -> Fill | None:
        """Try to fill a single order against a bar."""
        fill_price: Decimal | None = None

        if order.order_type == OrderType.MARKET:
            fill_price = bar.open

        elif order.order_type == OrderType.LIMIT:
            fill_price = self._check_limit(order, bar)

        elif order.order_type == OrderType.STOP:
            fill_price = self._check_stop(order, bar)

        elif order.order_type == OrderType.STOP_LIMIT:
            fill_price = self._check_stop_limit(order, bar)

        if fill_price is None:
            return None

        # Determine fill side for slippage
        fill_side = order.side
        if order.action in (OrderAction.EXIT, OrderAction.CLOSE):
            # Exiting a long = selling, exiting a short = buying
            fill_side = Side.SHORT if order.side == Side.LONG else Side.LONG

        # Apply slippage (only to market and stop orders)
        slippage_amount = Decimal("0")
        if order.order_type in (OrderType.MARKET, OrderType.STOP):
            adjusted_price = self._slippage.calculate(fill_price, fill_side)
            slippage_amount = abs(adjusted_price - fill_price)
            fill_price = adjusted_price

        # Calculate commission
        commission = self._commission.calculate(fill_price, order.quantity)

        return Fill(
            order_id=order.id,
            side=order.side,
            price=fill_price,
            quantity=order.quantity,
            commission=commission,
            slippage=slippage_amount,
            timestamp=bar.timestamp,
            tag=order.tag,
        )

    def _check_limit(self, order: Order, bar: OHLCV) -> Decimal | None:
        """Check if a LIMIT order can be filled."""
        if order.limit_price is None:
            return None

        if order.side == Side.LONG or order.action in (OrderAction.EXIT, OrderAction.CLOSE):
            # Buy limit: fills if price goes to or below limit
            if order.action == OrderAction.ENTRY and order.side == Side.LONG:
                if bar.low <= order.limit_price:
                    return order.limit_price
            # Sell limit (exit long): fills if price goes to or above limit
            elif order.action in (OrderAction.EXIT, OrderAction.CLOSE) and order.side == Side.LONG:
                if bar.high >= order.limit_price:
                    return order.limit_price
            # Sell limit (entry short): fills if price goes to or above limit
            elif order.action == OrderAction.ENTRY and order.side == Side.SHORT:
                if bar.high >= order.limit_price:
                    return order.limit_price
            # Buy limit (exit short): fills if price goes to or below limit
            elif order.action in (OrderAction.EXIT, OrderAction.CLOSE) and order.side == Side.SHORT:
                if bar.low <= order.limit_price:
                    return order.limit_price

        elif order.side == Side.SHORT:
            if bar.high >= order.limit_price:
                return order.limit_price

        return None

    def _check_stop(self, order: Order, bar: OHLCV) -> Decimal | None:
        """Check if a STOP order can be filled."""
        if order.stop_price is None:
            return None

        if order.side == Side.LONG and order.action == OrderAction.ENTRY:
            # Buy stop: fills when price rises to stop
            if bar.high >= order.stop_price:
                return max(bar.open, order.stop_price)
        elif order.side == Side.SHORT and order.action == OrderAction.ENTRY:
            # Sell stop: fills when price drops to stop
            if bar.low <= order.stop_price:
                return min(bar.open, order.stop_price)
        elif order.action in (OrderAction.EXIT, OrderAction.CLOSE):
            if order.side == Side.LONG:
                # Stop loss for long: sells when price drops to stop
                if bar.low <= order.stop_price:
                    return min(bar.open, order.stop_price)
            else:
                # Stop loss for short: buys when price rises to stop
                if bar.high >= order.stop_price:
                    return max(bar.open, order.stop_price)

        return None

    def _check_stop_limit(self, order: Order, bar: OHLCV) -> Decimal | None:
        """Check if a STOP_LIMIT order can be filled (simplified)."""
        # First check if stop is triggered, then check limit
        stop_triggered = self._check_stop(order, bar) is not None
        if stop_triggered and order.limit_price is not None:
            return self._check_limit(order, bar)
        return None
