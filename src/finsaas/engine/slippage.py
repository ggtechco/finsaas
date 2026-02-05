"""Slippage models for the backtest engine."""

from __future__ import annotations

import abc
from decimal import Decimal

from finsaas.core.types import Side


class SlippageModel(abc.ABC):
    """Base class for slippage calculation."""

    @abc.abstractmethod
    def calculate(self, price: Decimal, side: Side) -> Decimal:
        """Calculate slippage-adjusted fill price.

        Args:
            price: The base price (e.g., open of next bar).
            side: Trade direction.

        Returns:
            Adjusted price after slippage.
        """


class PercentageSlippage(SlippageModel):
    """Percentage-based slippage model."""

    def __init__(self, rate: Decimal = Decimal("0.0005")) -> None:
        self._rate = rate

    def calculate(self, price: Decimal, side: Side) -> Decimal:
        slippage = price * self._rate
        if side == Side.LONG:
            return price + slippage  # Buy higher
        else:
            return price - slippage  # Sell lower

    @property
    def rate(self) -> Decimal:
        return self._rate


class FixedSlippage(SlippageModel):
    """Fixed-point slippage model."""

    def __init__(self, points: Decimal = Decimal("0.01")) -> None:
        self._points = points

    def calculate(self, price: Decimal, side: Side) -> Decimal:
        if side == Side.LONG:
            return price + self._points
        else:
            return price - self._points


class ZeroSlippage(SlippageModel):
    """No slippage."""

    def calculate(self, price: Decimal, side: Side) -> Decimal:
        return price
