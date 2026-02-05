"""Data feed implementations for providing OHLCV bars to the backtest engine."""

from __future__ import annotations

import abc
from datetime import datetime
from decimal import Decimal
from typing import Iterator

from finsaas.core.types import OHLCV


class DataFeed(abc.ABC):
    """Abstract base class for data feeds."""

    @abc.abstractmethod
    def __iter__(self) -> Iterator[OHLCV]:
        """Iterate over bars in chronological order."""

    @abc.abstractmethod
    def __len__(self) -> int:
        """Total number of bars."""

    @property
    @abc.abstractmethod
    def symbol(self) -> str:
        """Symbol ticker."""

    @property
    @abc.abstractmethod
    def timeframe(self) -> str:
        """Timeframe string."""


class InMemoryFeed(DataFeed):
    """Data feed from a pre-loaded list of OHLCV bars."""

    def __init__(
        self, bars: list[OHLCV], symbol: str = "UNKNOWN", timeframe: str = "1h"
    ) -> None:
        self._bars = sorted(bars, key=lambda b: b.timestamp)
        self._symbol = symbol
        self._timeframe = timeframe

    def __iter__(self) -> Iterator[OHLCV]:
        return iter(self._bars)

    def __len__(self) -> int:
        return len(self._bars)

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def timeframe(self) -> str:
        return self._timeframe


class CSVFeed(DataFeed):
    """Data feed from a CSV file.

    Expected CSV format:
        timestamp,open,high,low,close,volume
        2023-01-01 00:00:00,100.00,105.00,99.00,103.00,1000
    """

    def __init__(
        self,
        filepath: str,
        symbol: str = "UNKNOWN",
        timeframe: str = "1h",
        timestamp_col: str = "timestamp",
        timestamp_format: str = "%Y-%m-%d %H:%M:%S",
    ) -> None:
        self._filepath = filepath
        self._symbol = symbol
        self._timeframe = timeframe
        self._timestamp_col = timestamp_col
        self._timestamp_format = timestamp_format
        self._bars: list[OHLCV] | None = None

    def _load(self) -> list[OHLCV]:
        if self._bars is not None:
            return self._bars

        import csv

        bars: list[OHLCV] = []
        with open(self._filepath, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bar = OHLCV(
                    timestamp=datetime.strptime(
                        row[self._timestamp_col], self._timestamp_format
                    ),
                    open=Decimal(row["open"]),
                    high=Decimal(row["high"]),
                    low=Decimal(row["low"]),
                    close=Decimal(row["close"]),
                    volume=Decimal(row.get("volume", "0")),
                )
                bars.append(bar)

        self._bars = sorted(bars, key=lambda b: b.timestamp)
        return self._bars

    def __iter__(self) -> Iterator[OHLCV]:
        return iter(self._load())

    def __len__(self) -> int:
        return len(self._load())

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def timeframe(self) -> str:
        return self._timeframe


class DatabaseFeed(DataFeed):
    """Data feed that reads from the PostgreSQL database."""

    def __init__(
        self,
        session_factory: object,
        symbol_id: int,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        symbol: str = "UNKNOWN",
    ) -> None:
        from sqlalchemy.orm import Session

        self._session_factory = session_factory
        self._symbol_id = symbol_id
        self._timeframe = timeframe
        self._start = start
        self._end = end
        self._symbol_str = symbol
        self._bars: list[OHLCV] | None = None

    def _load(self) -> list[OHLCV]:
        if self._bars is not None:
            return self._bars

        from sqlalchemy.orm import Session

        from finsaas.data.repository import OHLCVRepository

        session: Session = self._session_factory()  # type: ignore[operator]
        try:
            repo = OHLCVRepository(session)
            self._bars = repo.get_bars(
                self._symbol_id, self._timeframe, self._start, self._end
            )
        finally:
            session.close()

        return self._bars

    def __iter__(self) -> Iterator[OHLCV]:
        return iter(self._load())

    def __len__(self) -> int:
        return len(self._load())

    @property
    def symbol(self) -> str:
        return self._symbol_str

    @property
    def timeframe(self) -> str:
        return self._timeframe
