"""Strategy abstract base class - the foundation of the Python DSL."""

from __future__ import annotations

import abc
from decimal import Decimal
from typing import Any

from finsaas.core.context import BarContext
from finsaas.core.series import Series
from finsaas.core.types import OrderAction, OrderType, Side
from finsaas.engine.order import Order
from finsaas.strategy.parameters import ParamDescriptor
from finsaas.strategy.registry import register_strategy


class _SeriesAccessor:
    """Descriptor that lazily accesses a named series from the strategy's context."""

    def __init__(self, series_name: str) -> None:
        self._series_name = series_name

    def __get__(self, obj: Any, objtype: type = None) -> Any:
        if obj is None:
            return self
        ctx = obj._context
        assert ctx is not None, "Strategy not bound to EventLoop"
        return getattr(ctx, self._series_name)


class StrategyMeta(abc.ABCMeta):
    """Metaclass that auto-registers strategies and collects parameters."""

    def __new__(
        mcs, name: str, bases: tuple, namespace: dict, **kwargs: Any
    ) -> StrategyMeta:
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # Collect parameter descriptors
        params: dict[str, ParamDescriptor] = {}
        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, ParamDescriptor):
                attr_value.name = attr_name
                params[attr_name] = attr_value

        cls._param_descriptors = params  # type: ignore[attr-defined]

        # Auto-register non-abstract strategies
        if not getattr(cls, "__abstractmethods__", None) and name != "Strategy":
            register_strategy(cls)  # type: ignore[arg-type]

        return cls  # type: ignore[return-value]


class Strategy(abc.ABC, metaclass=StrategyMeta):
    """Abstract base class for all trading strategies.

    Subclass this to define a strategy using the Python DSL:

        class MyStrategy(Strategy):
            fast = IntParam(default=10, min_val=5, max_val=50)

            def on_init(self):
                self.fast_ma = self.create_series()

            def on_bar(self, ctx):
                self.fast_ma.current = self.ta.sma(self.close, self.fast)
    """

    _param_descriptors: dict[str, ParamDescriptor]

    # Built-in OHLCV series accessors (descriptors, not properties)
    # This avoids name collision with the close() method
    open = _SeriesAccessor("open")
    high = _SeriesAccessor("high")
    low = _SeriesAccessor("low")
    close = _SeriesAccessor("close")
    volume = _SeriesAccessor("volume")

    def __init__(self) -> None:
        self._loop: Any = None  # Set by _bind()
        self._context: BarContext | None = None

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def _bind(self, loop: Any) -> None:
        """Bind the strategy to an EventLoop instance."""
        self._loop = loop
        self._context = loop.context

    @property
    def bar_index(self) -> int:
        assert self._context is not None
        return self._context.bar_index

    @property
    def ta(self) -> Any:
        """Access technical analysis functions."""
        from finsaas.strategy.builtins import ta

        return ta

    # --- Series management ---

    def create_series(self, name: str = "") -> Series[Decimal]:
        """Create a new series registered with the context."""
        assert self._context is not None
        return self._context.create_series(name=name)

    # --- Order methods (Pine Script strategy.* equivalents) ---

    def entry(
        self,
        tag: str,
        side: Side,
        qty: Decimal = None,  # type: ignore[assignment]
        limit: Decimal = None,  # type: ignore[assignment]
        stop: Decimal = None,  # type: ignore[assignment]
        comment: str = "",
    ) -> None:
        """Submit an entry order (equivalent to strategy.entry in Pine Script).

        If qty is None, uses all available capital.
        """
        assert self._loop is not None and self._context is not None

        if qty is None:
            # Calculate quantity from available capital
            current_price = self._context.close.current
            if current_price > 0:
                portfolio = self._loop.portfolio
                qty = portfolio.cash / current_price
                # Use 99% to leave room for commission
                qty = (qty * Decimal("99")) / Decimal("100")
            else:
                qty = Decimal("0")

        order_type = OrderType.MARKET
        if limit is not None and stop is not None:
            order_type = OrderType.STOP_LIMIT
        elif limit is not None:
            order_type = OrderType.LIMIT
        elif stop is not None:
            order_type = OrderType.STOP

        order = Order(
            action=OrderAction.ENTRY,
            side=side,
            order_type=order_type,
            quantity=qty,
            limit_price=limit,
            stop_price=stop,
            tag=tag,
        )
        self._loop.submit_order(order, OrderAction.ENTRY)

    def exit(
        self,
        tag: str,
        from_entry: str = "",
        qty: Decimal = None,  # type: ignore[assignment]
        limit: Decimal = None,  # type: ignore[assignment]
        stop: Decimal = None,  # type: ignore[assignment]
        comment: str = "",
    ) -> None:
        """Submit an exit order (equivalent to strategy.exit in Pine Script)."""
        assert self._loop is not None

        # Look up the position to determine side and qty
        position = self._loop.portfolio.get_position(from_entry or tag)
        if position is None:
            return  # No position to exit

        if qty is None:
            qty = position.quantity

        order_type = OrderType.MARKET
        if limit is not None and stop is not None:
            order_type = OrderType.STOP_LIMIT
        elif limit is not None:
            order_type = OrderType.LIMIT
        elif stop is not None:
            order_type = OrderType.STOP

        order = Order(
            action=OrderAction.EXIT,
            side=position.side,
            order_type=order_type,
            quantity=qty,
            limit_price=limit,
            stop_price=stop,
            tag=from_entry or tag,
        )
        self._loop.submit_order(order, OrderAction.EXIT)

    def close_position(self, tag: str, comment: str = "") -> None:
        """Close a position immediately at market (equivalent to strategy.close)."""
        assert self._loop is not None

        position = self._loop.portfolio.get_position(tag)
        if position is None:
            return

        order = Order(
            action=OrderAction.CLOSE,
            side=position.side,
            order_type=OrderType.MARKET,
            quantity=position.quantity,
            tag=tag,
        )
        self._loop.submit_order(order, OrderAction.CLOSE)

    def close_all(self, comment: str = "") -> None:
        """Close all open positions."""
        assert self._loop is not None
        for tag in list(self._loop.portfolio.positions.keys()):
            self.close_position(tag, comment=comment)

    # --- Parameter management ---

    def get_parameters(self) -> dict[str, object]:
        """Get current parameter values as a dict."""
        params: dict[str, object] = {}
        for param_name in self._param_descriptors:
            params[param_name] = getattr(self, param_name)
        return params

    def set_parameters(self, params: dict[str, object]) -> None:
        """Set parameter values from a dict."""
        for param_name, value in params.items():
            if param_name in self._param_descriptors:
                setattr(self, param_name, value)

    # --- Abstract methods ---

    def on_init(self) -> None:
        """Called once before the backtest starts. Override to initialize indicators."""

    @abc.abstractmethod
    def on_bar(self, ctx: BarContext) -> None:
        """Called for each bar. Override to implement trading logic."""
