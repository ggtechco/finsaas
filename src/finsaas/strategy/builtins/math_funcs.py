"""Math utility functions matching Pine Script's math.* namespace."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def abs_val(x: Decimal) -> Decimal:
    """Absolute value. Pine Script: math.abs(x)"""
    return abs(x)


def max_val(a: Decimal, b: Decimal) -> Decimal:
    """Maximum of two values. Pine Script: math.max(a, b)"""
    return max(a, b)


def min_val(a: Decimal, b: Decimal) -> Decimal:
    """Minimum of two values. Pine Script: math.min(a, b)"""
    return min(a, b)


def round_val(x: Decimal, precision: int = 0) -> Decimal:
    """Round to given decimal places. Pine Script: math.round(x, precision)"""
    if precision == 0:
        return x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    quant = Decimal(10) ** -precision
    return x.quantize(quant, rounding=ROUND_HALF_UP)


def ceil(x: Decimal) -> Decimal:
    """Ceiling. Pine Script: math.ceil(x)"""
    import math as _math
    return Decimal(str(_math.ceil(float(x))))


def floor(x: Decimal) -> Decimal:
    """Floor. Pine Script: math.floor(x)"""
    import math as _math
    return Decimal(str(_math.floor(float(x))))


def sign(x: Decimal) -> int:
    """Sign of value: -1, 0, or 1. Pine Script: math.sign(x)"""
    if x > 0:
        return 1
    elif x < 0:
        return -1
    return 0


def pow_val(base: Decimal, exp: Decimal) -> Decimal:
    """Power. Pine Script: math.pow(base, exp)"""
    return Decimal(str(float(base) ** float(exp)))


def sqrt(x: Decimal) -> Decimal:
    """Square root. Pine Script: math.sqrt(x)"""
    if x <= 0:
        return Decimal("0")
    # Newton's method
    guess = x
    while True:
        new_guess = (guess + x / guess) / Decimal("2")
        if abs(new_guess - guess) < Decimal("1E-20"):
            break
        guess = new_guess
    return guess


def log(x: Decimal) -> Decimal:
    """Natural logarithm. Pine Script: math.log(x)"""
    import math as _math
    if x <= 0:
        return Decimal("0")
    return Decimal(str(_math.log(float(x))))


def exp(x: Decimal) -> Decimal:
    """Exponential. Pine Script: math.exp(x)"""
    import math as _math
    return Decimal(str(_math.exp(float(x))))
