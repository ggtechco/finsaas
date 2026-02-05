"""Strategy operations module - Pine Script strategy.* function equivalents.

These functions provide a functional interface to strategy operations,
complementing the OOP approach in the Strategy base class.
"""

from __future__ import annotations

from decimal import Decimal

from finsaas.core.types import Side


def calc_position_size(
    capital: Decimal,
    price: Decimal,
    risk_pct: Decimal = Decimal("2"),
    stop_distance: Decimal | None = None,
) -> Decimal:
    """Calculate position size based on risk percentage.

    Args:
        capital: Available capital.
        price: Entry price.
        risk_pct: Maximum risk as percentage of capital.
        stop_distance: Distance to stop loss in price units.

    Returns:
        Position size (quantity).
    """
    risk_amount = capital * risk_pct / Decimal("100")
    if stop_distance and stop_distance > 0:
        return risk_amount / stop_distance
    if price > 0:
        return risk_amount / price
    return Decimal("0")


def percent_of_equity(equity: Decimal, pct: Decimal, price: Decimal) -> Decimal:
    """Calculate quantity as a percentage of equity.

    Args:
        equity: Total equity.
        pct: Percentage (e.g., 50 for 50%).
        price: Current price.

    Returns:
        Quantity.
    """
    if price <= 0:
        return Decimal("0")
    return (equity * pct / Decimal("100")) / price
