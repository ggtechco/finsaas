"""Portfolio management - position tracking and equity curve computation."""

from __future__ import annotations

import structlog
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from finsaas.core.types import OHLCV, OrderAction, Side, TradeResult
from finsaas.engine.order import Fill, Position

logger = structlog.get_logger()


@dataclass
class EquityPoint:
    """A single point on the equity curve."""

    bar_index: int
    timestamp: datetime
    equity: Decimal
    cash: Decimal
    position_value: Decimal
    drawdown: Decimal = Decimal("0")


class Portfolio:
    """Tracks positions, cash, and equity over time.

    Manages:
    - Open/closed positions
    - Cash balance
    - Equity curve computation
    - Trade result generation
    """

    def __init__(self, initial_capital: Decimal = Decimal("10000")) -> None:
        self._initial_capital = initial_capital
        self._cash = initial_capital
        self._positions: dict[str, Position] = {}  # tag -> Position
        self._closed_positions: list[Position] = []
        self._equity_curve: list[EquityPoint] = []
        self._peak_equity = initial_capital
        self._trade_results: list[TradeResult] = []

    @property
    def cash(self) -> Decimal:
        return self._cash

    @property
    def initial_capital(self) -> Decimal:
        return self._initial_capital

    @property
    def positions(self) -> dict[str, Position]:
        return dict(self._positions)

    @property
    def open_position_count(self) -> int:
        return len(self._positions)

    @property
    def closed_positions(self) -> list[Position]:
        return list(self._closed_positions)

    @property
    def equity_curve(self) -> list[EquityPoint]:
        return list(self._equity_curve)

    @property
    def trade_results(self) -> list[TradeResult]:
        return list(self._trade_results)

    def get_position(self, tag: str) -> Position | None:
        return self._positions.get(tag)

    def has_position(self, tag: str) -> bool:
        return tag in self._positions

    def equity(self, current_price: Decimal) -> Decimal:
        """Calculate total equity (cash + unrealized positions)."""
        position_value = self._position_value(current_price)
        return self._cash + position_value

    def _position_value(self, current_price: Decimal) -> Decimal:
        """Calculate total value of open positions."""
        total = Decimal("0")
        for pos in self._positions.values():
            if pos.is_long:
                total += current_price * pos.quantity
            else:
                # Short position: value = entry_value + unrealized_pnl
                total += pos.entry_price * pos.quantity + pos.unrealized_pnl(current_price)
        return total

    def process_fill(self, fill: Fill, action: OrderAction, bar_index: int) -> None:
        """Process a fill event and update positions/cash."""
        tag = fill.tag or "default"

        if action == OrderAction.ENTRY:
            self._open_position(fill, bar_index, tag)
        elif action == OrderAction.EXIT:
            self._close_position(fill, bar_index, tag)
        elif action == OrderAction.CLOSE:
            self._close_position(fill, bar_index, tag)

    def _open_position(self, fill: Fill, bar_index: int, tag: str) -> None:
        """Open a new position from a fill."""
        # If there's already a position with this tag, close it first
        if tag in self._positions:
            existing = self._positions[tag]
            if existing.side != fill.side:
                # Reverse position: close existing, open new
                self._force_close(tag, fill.price, fill.timestamp, bar_index, fill.commission)
            else:
                # Same direction - add to position (average)
                logger.warning("duplicate_entry", tag=tag, side=fill.side.value)
                return

        cost = fill.price * fill.quantity
        if fill.side == Side.LONG:
            self._cash -= cost + fill.commission
        else:
            # Short entry: receive the sale amount
            self._cash += cost - fill.commission

        position = Position(
            side=fill.side,
            entry_price=fill.price,
            quantity=fill.quantity,
            entry_time=fill.timestamp,
            entry_bar=bar_index,
            tag=tag,
            commission_entry=fill.commission,
        )
        self._positions[tag] = position
        logger.debug("position_opened", tag=tag, side=fill.side.value,
                     price=str(fill.price), qty=str(fill.quantity))

    def _close_position(self, fill: Fill, bar_index: int, tag: str) -> None:
        """Close an existing position."""
        if tag not in self._positions:
            logger.warning("no_position_to_close", tag=tag)
            return

        self._force_close(tag, fill.price, fill.timestamp, bar_index, fill.commission, fill.tag)

    def _force_close(
        self,
        tag: str,
        price: Decimal,
        timestamp: datetime,
        bar_index: int,
        commission: Decimal,
        exit_tag: str = "",
    ) -> None:
        """Force-close a position and record the trade."""
        position = self._positions.pop(tag)
        pnl = position.close(price, timestamp, bar_index, exit_tag, commission)

        # Update cash
        if position.is_long:
            self._cash += price * position.quantity - commission
        else:
            # Close short: buy back
            self._cash -= price * position.quantity + commission

        self._closed_positions.append(position)

        # Record trade result
        trade = TradeResult(
            entry_time=position.entry_time,
            exit_time=timestamp,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=price,
            quantity=position.quantity,
            pnl=position.pnl or Decimal("0"),
            pnl_pct=position.pnl_pct or Decimal("0"),
            commission=position.commission_entry + position.commission_exit,
            bars_held=position.bars_held or 0,
            entry_tag=tag,
            exit_tag=exit_tag,
        )
        self._trade_results.append(trade)
        logger.debug("position_closed", tag=tag, pnl=str(pnl))

    def record_equity(self, bar: OHLCV, bar_index: int) -> EquityPoint:
        """Record equity at the current bar."""
        current_price = bar.close
        pos_value = self._position_value(current_price)
        total_equity = self._cash + pos_value

        if total_equity > self._peak_equity:
            self._peak_equity = total_equity

        drawdown = Decimal("0")
        if self._peak_equity > 0:
            drawdown = (self._peak_equity - total_equity) / self._peak_equity

        point = EquityPoint(
            bar_index=bar_index,
            timestamp=bar.timestamp,
            equity=total_equity,
            cash=self._cash,
            position_value=pos_value,
            drawdown=drawdown,
        )
        self._equity_curve.append(point)
        return point

    def close_all_positions(self, price: Decimal, timestamp: datetime, bar_index: int) -> None:
        """Close all open positions (used at end of backtest)."""
        tags = list(self._positions.keys())
        for tag in tags:
            self._force_close(tag, price, timestamp, bar_index, Decimal("0"), "backtest_end")
