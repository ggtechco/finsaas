"""Pine Script-style Series[T] implementation.

The Series class models Pine Script's series semantics:
- Each bar appends a new value
- Historical values are accessed via [] operator: close[1] = previous bar's close
- Uses a deque-based ring buffer for bounded memory
- Supports commit/rollback for transactional bar processing
"""

from __future__ import annotations

from collections import deque
from decimal import Decimal
from typing import Generic, TypeVar, overload

from finsaas.core.errors import InsufficientDataError, SeriesIndexError

T = TypeVar("T")

_SENTINEL = object()


class Series(Generic[T]):
    """Pine Script-compatible Series with history buffer.

    The series maintains a ring buffer of historical values.
    The most recent value (index 0) is the 'current' value.
    Index 1 is the previous bar's value, etc.

    Usage:
        s = Series[Decimal](max_bars_back=5000)
        s.current = Decimal("100")
        s.commit()
        s.current = Decimal("101")
        s.commit()
        assert s[0] == Decimal("101")  # current
        assert s[1] == Decimal("100")  # previous
    """

    __slots__ = ("_buffer", "_max_bars_back", "_current", "_committed", "_name")

    def __init__(self, max_bars_back: int = 5000, name: str = "") -> None:
        self._buffer: deque[T] = deque(maxlen=max_bars_back)
        self._max_bars_back = max_bars_back
        self._current: T | object = _SENTINEL
        self._committed = False
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def current(self) -> T:
        """Get the current (uncommitted) value."""
        if self._current is _SENTINEL:
            if len(self._buffer) == 0:
                raise SeriesIndexError(
                    f"Series '{self._name}': no current value set and no history"
                )
            return self._buffer[0]
        return self._current  # type: ignore[return-value]

    @current.setter
    def current(self, value: T) -> None:
        """Set the current bar's value."""
        self._current = value
        self._committed = False

    def commit(self) -> None:
        """Commit the current value to history buffer.

        Called at the end of each bar to finalize the value.
        If no current value was set, commits NaN/None depending on type.
        """
        if self._current is _SENTINEL:
            # No value set this bar - propagate last value or None
            if len(self._buffer) > 0:
                self._buffer.appendleft(self._buffer[0])
            else:
                self._buffer.appendleft(None)  # type: ignore[arg-type]
        else:
            self._buffer.appendleft(self._current)  # type: ignore[arg-type]
        self._current = _SENTINEL
        self._committed = True

    def rollback(self) -> None:
        """Discard the current uncommitted value."""
        self._current = _SENTINEL

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> list[T]: ...

    def __getitem__(self, index: int | slice) -> T | list[T]:
        """Access historical values. Index 0 = current/most recent committed."""
        if isinstance(index, slice):
            start = index.start or 0
            stop = index.stop or len(self._buffer)
            step = index.step or 1
            return [self._get_single(i) for i in range(start, stop, step)]

        return self._get_single(index)

    def _get_single(self, index: int) -> T:
        if index == 0 and self._current is not _SENTINEL:
            return self._current  # type: ignore[return-value]

        # Adjust index: if current is set but uncommitted, index 0 is current,
        # and index 1+ maps to buffer[0+]
        buf_index = index
        if self._current is not _SENTINEL and index > 0:
            buf_index = index - 1

        if buf_index < 0:
            raise SeriesIndexError(f"Series '{self._name}': negative index {index}")
        if buf_index >= len(self._buffer):
            raise InsufficientDataError(
                f"Series '{self._name}': index {index} requires at least "
                f"{buf_index + 1} bars, but only {len(self._buffer)} available"
            )
        return self._buffer[buf_index]

    def __len__(self) -> int:
        """Number of committed values in the buffer."""
        return len(self._buffer)

    def __bool__(self) -> bool:
        """True if series has any data."""
        return len(self._buffer) > 0 or self._current is not _SENTINEL

    def __repr__(self) -> str:
        name = f"'{self._name}'" if self._name else ""
        cur = self._current if self._current is not _SENTINEL else "unset"
        return f"Series({name}, current={cur}, len={len(self._buffer)})"


def na(value: T | None) -> bool:
    """Check if a value is NaN or None (Pine Script's na())."""
    if value is None:
        return True
    if isinstance(value, Decimal):
        return value.is_nan()
    if isinstance(value, float):
        import math

        return math.isnan(value)
    return False


def nz(value: T | None, replacement: T | None = None) -> T:
    """Replace NaN/None with a replacement value (Pine Script's nz()).

    If replacement is None, uses zero for numeric types.
    """
    if na(value):
        if replacement is not None:
            return replacement  # type: ignore[return-value]
        if isinstance(value, Decimal) or value is None:
            return Decimal("0")  # type: ignore[return-value]
        return type(value)(0)  # type: ignore[return-value, call-arg]
    return value  # type: ignore[return-value]


def fixnan(series: Series[T]) -> T:
    """Replace NaN with last non-NaN value in series (Pine Script's fixnan())."""
    for i in range(len(series)):
        val = series[i]
        if not na(val):
            return val
    return Decimal("0")  # type: ignore[return-value]
