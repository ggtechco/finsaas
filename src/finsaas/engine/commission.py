"""Commission models for the backtest engine."""

from __future__ import annotations

import abc
from decimal import Decimal


class CommissionModel(abc.ABC):
    """Base class for commission calculation."""

    @abc.abstractmethod
    def calculate(self, price: Decimal, quantity: Decimal) -> Decimal:
        """Calculate commission for a trade."""


class PercentageCommission(CommissionModel):
    """Percentage-based commission (e.g., 0.1% of trade value)."""

    def __init__(self, rate: Decimal = Decimal("0.001")) -> None:
        self._rate = rate

    def calculate(self, price: Decimal, quantity: Decimal) -> Decimal:
        return price * quantity * self._rate

    @property
    def rate(self) -> Decimal:
        return self._rate


class FixedCommission(CommissionModel):
    """Fixed commission per trade."""

    def __init__(self, amount: Decimal = Decimal("1.0")) -> None:
        self._amount = amount

    def calculate(self, price: Decimal, quantity: Decimal) -> Decimal:
        return self._amount


class TieredCommission(CommissionModel):
    """Tiered commission based on trade value."""

    def __init__(self, tiers: list[tuple[Decimal, Decimal]]) -> None:
        """
        Args:
            tiers: List of (threshold, rate) tuples, sorted ascending by threshold.
                   The rate is applied to the trade value below that threshold.
        """
        self._tiers = sorted(tiers, key=lambda t: t[0])

    def calculate(self, price: Decimal, quantity: Decimal) -> Decimal:
        value = price * quantity
        for threshold, rate in reversed(self._tiers):
            if value >= threshold:
                return value * rate
        # Below all thresholds - use first tier rate
        return value * self._tiers[0][1] if self._tiers else Decimal("0")


class ZeroCommission(CommissionModel):
    """No commission."""

    def calculate(self, price: Decimal, quantity: Decimal) -> Decimal:
        return Decimal("0")
