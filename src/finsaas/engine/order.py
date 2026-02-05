"""Order, Fill, and Position data classes for the backtest engine."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from finsaas.core.types import OrderAction, OrderStatus, OrderType, PositionStatus, Side


@dataclass
class Order:
    """Represents a pending order in the simulation."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    action: OrderAction = OrderAction.ENTRY
    side: Side = Side.LONG
    order_type: OrderType = OrderType.MARKET
    quantity: Decimal = Decimal("0")
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    status: OrderStatus = OrderStatus.PENDING
    tag: str = ""
    created_bar: int = -1
    created_at: datetime | None = None
    filled_at: datetime | None = None
    fill_price: Decimal | None = None
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")

    def cancel(self) -> None:
        self.status = OrderStatus.CANCELLED

    def reject(self, reason: str = "") -> None:
        self.status = OrderStatus.REJECTED

    @property
    def is_pending(self) -> bool:
        return self.status == OrderStatus.PENDING

    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED


@dataclass
class Fill:
    """Result of an order being executed."""

    order_id: str
    side: Side
    price: Decimal
    quantity: Decimal
    commission: Decimal
    slippage: Decimal
    timestamp: datetime
    tag: str = ""


@dataclass
class Position:
    """Tracks an open position."""

    side: Side
    entry_price: Decimal
    quantity: Decimal
    entry_time: datetime
    entry_bar: int
    tag: str = ""
    status: PositionStatus = PositionStatus.OPEN
    exit_price: Decimal | None = None
    exit_time: datetime | None = None
    exit_bar: int | None = None
    exit_tag: str = ""
    commission_entry: Decimal = Decimal("0")
    commission_exit: Decimal = Decimal("0")

    @property
    def is_open(self) -> bool:
        return self.status == PositionStatus.OPEN

    @property
    def is_long(self) -> bool:
        return self.side == Side.LONG

    @property
    def is_short(self) -> bool:
        return self.side == Side.SHORT

    def unrealized_pnl(self, current_price: Decimal) -> Decimal:
        """Calculate unrealized P&L at the given price."""
        if self.is_long:
            return (current_price - self.entry_price) * self.quantity
        else:
            return (self.entry_price - current_price) * self.quantity

    def close(
        self,
        exit_price: Decimal,
        exit_time: datetime,
        exit_bar: int,
        exit_tag: str = "",
        commission: Decimal = Decimal("0"),
    ) -> Decimal:
        """Close the position and return realized P&L."""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.exit_bar = exit_bar
        self.exit_tag = exit_tag
        self.commission_exit = commission
        self.status = PositionStatus.CLOSED

        if self.is_long:
            gross_pnl = (exit_price - self.entry_price) * self.quantity
        else:
            gross_pnl = (self.entry_price - exit_price) * self.quantity

        return gross_pnl - self.commission_entry - self.commission_exit

    @property
    def bars_held(self) -> int | None:
        if self.exit_bar is not None:
            return self.exit_bar - self.entry_bar
        return None

    @property
    def pnl(self) -> Decimal | None:
        """Realized P&L (only available for closed positions)."""
        if self.exit_price is None:
            return None
        if self.is_long:
            gross = (self.exit_price - self.entry_price) * self.quantity
        else:
            gross = (self.entry_price - self.exit_price) * self.quantity
        return gross - self.commission_entry - self.commission_exit

    @property
    def pnl_pct(self) -> Decimal | None:
        """Realized P&L percentage."""
        if self.pnl is None:
            return None
        cost_basis = self.entry_price * self.quantity
        if cost_basis == 0:
            return Decimal("0")
        return (self.pnl / cost_basis) * Decimal("100")
