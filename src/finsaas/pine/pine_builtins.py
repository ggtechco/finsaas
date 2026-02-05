"""Pine Script built-in function implementations.

Maps Pine Script built-in functions to their Python implementations
for use during transpiled strategy execution.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from finsaas.core.series import Series, na, nz


def pine_nz(value: Any, replacement: Any = None) -> Any:
    """Pine Script nz() function."""
    return nz(value, replacement)


def pine_na(value: Any) -> bool:
    """Pine Script na() function."""
    return na(value)


def pine_abs(x: Decimal) -> Decimal:
    """Pine Script math.abs()."""
    return abs(x)


def pine_max(a: Decimal, b: Decimal) -> Decimal:
    """Pine Script math.max()."""
    return max(a, b)


def pine_min(a: Decimal, b: Decimal) -> Decimal:
    """Pine Script math.min()."""
    return min(a, b)


def pine_round(x: Decimal, precision: int = 0) -> Decimal:
    """Pine Script math.round()."""
    from finsaas.strategy.builtins.math_funcs import round_val
    return round_val(x, precision)


def pine_tostring(value: Any) -> str:
    """Pine Script str.tostring()."""
    return str(value)


def pine_color(name: str) -> str:
    """Map Pine Script color names to hex values."""
    colors = {
        "red": "#FF0000",
        "green": "#00FF00",
        "blue": "#0000FF",
        "white": "#FFFFFF",
        "black": "#000000",
        "orange": "#FFA500",
        "purple": "#800080",
        "yellow": "#FFFF00",
        "aqua": "#00FFFF",
        "lime": "#00FF00",
        "silver": "#C0C0C0",
        "gray": "#808080",
        "navy": "#000080",
        "teal": "#008080",
        "maroon": "#800000",
    }
    return colors.get(name, "#000000")
