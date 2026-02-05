"""Core type definitions for the backtest engine."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import NamedTuple


class Side(enum.Enum):
    """Trade direction."""

    LONG = "long"
    SHORT = "short"


class OrderType(enum.Enum):
    """Order execution type."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderAction(enum.Enum):
    """Order action type."""

    ENTRY = "entry"
    EXIT = "exit"
    CLOSE = "close"


class OrderStatus(enum.Enum):
    """Order lifecycle status."""

    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class PositionStatus(enum.Enum):
    """Position status."""

    OPEN = "open"
    CLOSED = "closed"


class Timeframe(enum.Enum):
    """Supported timeframes."""

    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1D"
    W1 = "1W"
    MN1 = "1M"


class BarState(enum.Enum):
    """Current bar processing state in the event loop."""

    NEW = "new"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"


class OHLCV(NamedTuple):
    """Single OHLCV bar data using Decimal for deterministic arithmetic."""

    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass(frozen=True)
class SymbolInfo:
    """Symbol metadata."""

    ticker: str
    exchange: str = ""
    asset_type: str = "crypto"
    tick_size: Decimal = Decimal("0.01")
    lot_size: Decimal = Decimal("0.001")
    base_currency: str = "USD"
    quote_currency: str = "USD"


@dataclass(frozen=True)
class TradeResult:
    """Result of a completed round-trip trade."""

    entry_time: datetime
    exit_time: datetime
    side: Side
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    pnl: Decimal
    pnl_pct: Decimal
    commission: Decimal
    bars_held: int
    entry_tag: str = ""
    exit_tag: str = ""
