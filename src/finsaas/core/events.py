"""Event definitions for the event-driven simulation loop."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from finsaas.core.types import OHLCV, OrderAction, OrderType, Side


class EventType(enum.Enum):
    """Event types in the simulation pipeline."""

    MARKET = "market"
    SIGNAL = "signal"
    ORDER = "order"
    FILL = "fill"


@dataclass(frozen=True)
class MarketEvent:
    """New bar data available."""

    type: EventType = field(default=EventType.MARKET, init=False)
    bar: OHLCV
    bar_index: int
    symbol: str


@dataclass(frozen=True)
class SignalEvent:
    """Strategy generated a trading signal."""

    type: EventType = field(default=EventType.SIGNAL, init=False)
    timestamp: datetime
    action: OrderAction
    side: Side
    order_type: OrderType = OrderType.MARKET
    tag: str = ""
    quantity: Decimal | None = None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    comment: str = ""


@dataclass(frozen=True)
class OrderEvent:
    """Order submitted to the broker."""

    type: EventType = field(default=EventType.ORDER, init=False)
    timestamp: datetime
    order_id: str
    action: OrderAction
    side: Side
    order_type: OrderType
    quantity: Decimal
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    tag: str = ""


@dataclass(frozen=True)
class FillEvent:
    """Order has been filled."""

    type: EventType = field(default=EventType.FILL, init=False)
    timestamp: datetime
    order_id: str
    side: Side
    fill_price: Decimal
    quantity: Decimal
    commission: Decimal
    slippage: Decimal
    tag: str = ""
