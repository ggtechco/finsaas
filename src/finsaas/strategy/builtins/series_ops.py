"""Series operations - Pine Script series utility functions."""

from __future__ import annotations

from decimal import Decimal

from finsaas.core.series import Series, na, nz, fixnan

# Re-export for convenience
__all__ = ["na", "nz", "fixnan", "valuewhen", "barssince"]


def valuewhen(condition: bool, source: Series[Decimal], occurrence: int = 0) -> Decimal:
    """Return the value of source when condition was last true.

    Pine Script equivalent: ta.valuewhen(condition, source, occurrence)
    Note: Simplified - only checks current bar.
    """
    if condition:
        return source.current
    # Would need historical condition tracking for full implementation
    return nz(source.current)


def barssince(condition: bool) -> int:
    """Number of bars since condition was last true.

    Note: Simplified - requires external tracking for full implementation.
    """
    if condition:
        return 0
    return -1  # Indicates condition never true in available data
