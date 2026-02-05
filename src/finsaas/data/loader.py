"""Data loading utilities for importing OHLCV data."""

from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from finsaas.data.models import OHLCVBar
from finsaas.data.repository import OHLCVRepository, SymbolRepository


def load_csv_to_db(
    session: Session,
    filepath: str | Path,
    ticker: str,
    timeframe: str,
    exchange: str = "",
    timestamp_col: str = "timestamp",
    timestamp_format: str = "%Y-%m-%d %H:%M:%S",
) -> int:
    """Load OHLCV data from CSV file into the database.

    Returns the number of bars inserted.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    symbol_repo = SymbolRepository(session)
    ohlcv_repo = OHLCVRepository(session)

    symbol = symbol_repo.get_or_create(ticker=ticker, exchange=exchange)

    bars: list[OHLCVBar] = []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bar = OHLCVBar(
                symbol_id=symbol.id,
                timeframe=timeframe,
                timestamp=datetime.strptime(row[timestamp_col], timestamp_format),
                open=Decimal(row["open"]),
                high=Decimal(row["high"]),
                low=Decimal(row["low"]),
                close=Decimal(row["close"]),
                volume=Decimal(row.get("volume", "0")),
            )
            bars.append(bar)

    count = ohlcv_repo.bulk_insert(bars)
    session.commit()
    return count
