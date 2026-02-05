"""BarContext - per-bar state container for strategy execution."""

from __future__ import annotations

from decimal import Decimal

from finsaas.core.series import Series
from finsaas.core.types import OHLCV, BarState, SymbolInfo, Timeframe


class BarContext:
    """Context object passed to strategy.on_bar() each iteration.

    Maintains OHLCV built-in series and bar metadata.
    Updated by the EventLoop at the start of each bar.
    """

    __slots__ = (
        "_bar_index",
        "_bar_state",
        "_symbol_info",
        "_timeframe",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "time",
        "_current_bar",
        "_series_registry",
    )

    def __init__(
        self,
        symbol_info: SymbolInfo,
        timeframe: Timeframe,
        max_bars_back: int = 5000,
    ) -> None:
        self._bar_index = -1
        self._bar_state = BarState.NEW
        self._symbol_info = symbol_info
        self._timeframe = timeframe
        self._current_bar: OHLCV | None = None

        # Built-in OHLCV series
        self.open: Series[Decimal] = Series(max_bars_back=max_bars_back, name="open")
        self.high: Series[Decimal] = Series(max_bars_back=max_bars_back, name="high")
        self.low: Series[Decimal] = Series(max_bars_back=max_bars_back, name="low")
        self.close: Series[Decimal] = Series(max_bars_back=max_bars_back, name="close")
        self.volume: Series[Decimal] = Series(max_bars_back=max_bars_back, name="volume")
        self.time: Series[int] = Series(max_bars_back=max_bars_back, name="time")

        # Track all series for batch commit/rollback
        self._series_registry: list[Series] = [  # type: ignore[type-arg]
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
            self.time,
        ]

    @property
    def bar_index(self) -> int:
        return self._bar_index

    @property
    def bar_state(self) -> BarState:
        return self._bar_state

    @property
    def symbol_info(self) -> SymbolInfo:
        return self._symbol_info

    @property
    def timeframe(self) -> Timeframe:
        return self._timeframe

    @property
    def current_bar(self) -> OHLCV | None:
        return self._current_bar

    def register_series(self, series: Series) -> None:  # type: ignore[type-arg]
        """Register a user-created series for automatic commit/rollback."""
        self._series_registry.append(series)

    def create_series(
        self, name: str = "", max_bars_back: int = 5000
    ) -> Series[Decimal]:
        """Create and register a new series."""
        s: Series[Decimal] = Series(max_bars_back=max_bars_back, name=name)
        self.register_series(s)
        return s

    def update(self, bar: OHLCV, bar_index: int) -> None:
        """Update context with new bar data.

        Called by EventLoop at start of each bar iteration.
        """
        self._current_bar = bar
        self._bar_index = bar_index
        self._bar_state = BarState.NEW

        # Update built-in OHLCV series with current bar values
        self.open.current = bar.open
        self.high.current = bar.high
        self.low.current = bar.low
        self.close.current = bar.close
        self.volume.current = bar.volume
        self.time.current = int(bar.timestamp.timestamp())

    def commit_all(self) -> None:
        """Commit all registered series. Called at end of bar processing."""
        for series in self._series_registry:
            series.commit()
        self._bar_state = BarState.CONFIRMED

    def rollback_all(self) -> None:
        """Rollback all registered series. Called on error."""
        for series in self._series_registry:
            series.rollback()
