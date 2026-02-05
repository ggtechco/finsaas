"""Risk control checks for order validation."""

from __future__ import annotations

import abc
from decimal import Decimal

from finsaas.core.errors import InsufficientCapitalError, RiskLimitError
from finsaas.engine.order import Order


class RiskCheck(abc.ABC):
    """Base class for risk checks applied before order execution."""

    @abc.abstractmethod
    def validate(
        self,
        order: Order,
        cash: Decimal,
        equity: Decimal,
        current_price: Decimal,
    ) -> None:
        """Validate the order. Raise an exception if rejected."""


class MaxPositionSizeCheck(RiskCheck):
    """Reject orders that would exceed a maximum position size as % of equity."""

    def __init__(self, max_pct: Decimal = Decimal("100")) -> None:
        self._max_pct = max_pct

    def validate(
        self,
        order: Order,
        cash: Decimal,
        equity: Decimal,
        current_price: Decimal,
    ) -> None:
        order_value = current_price * order.quantity
        pct_of_equity = (order_value / equity * Decimal("100")) if equity > 0 else Decimal("0")
        if pct_of_equity > self._max_pct:
            raise RiskLimitError(
                f"Order value ({pct_of_equity:.1f}% of equity) exceeds "
                f"max position size ({self._max_pct}%)"
            )


class SufficientCapitalCheck(RiskCheck):
    """Ensure there's enough cash to execute the order."""

    def validate(
        self,
        order: Order,
        cash: Decimal,
        equity: Decimal,
        current_price: Decimal,
    ) -> None:
        required = current_price * order.quantity
        if required > cash:
            raise InsufficientCapitalError(
                f"Order requires {required} but only {cash} available"
            )


class MaxDrawdownCheck(RiskCheck):
    """Halt trading if drawdown exceeds threshold."""

    def __init__(
        self, max_dd_pct: Decimal = Decimal("50"), initial_capital: Decimal = Decimal("10000")
    ) -> None:
        self._max_dd_pct = max_dd_pct
        self._initial_capital = initial_capital
        self._peak_equity = initial_capital

    def validate(
        self,
        order: Order,
        cash: Decimal,
        equity: Decimal,
        current_price: Decimal,
    ) -> None:
        if equity > self._peak_equity:
            self._peak_equity = equity

        if self._peak_equity > 0:
            dd_pct = ((self._peak_equity - equity) / self._peak_equity) * Decimal("100")
            if dd_pct > self._max_dd_pct:
                raise RiskLimitError(
                    f"Drawdown ({dd_pct:.1f}%) exceeds max ({self._max_dd_pct}%)"
                )
