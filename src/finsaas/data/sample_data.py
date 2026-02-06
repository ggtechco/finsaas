"""Generate realistic sample OHLCV data for dashboard seeding."""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta


def generate_sample_ohlcv(bars: int = 500, seed: int = 42) -> list[list[str]]:
    """Generate realistic BTCUSDT-like 1h OHLCV data.

    Uses a deterministic random walk with trend and volatility clustering
    to produce plausible price action around the 30000-35000 range.

    Returns a list of rows: [timestamp, open, high, low, close, volume].
    """
    rng = random.Random(seed)

    price = 31500.0
    base_vol = 0.0015  # ~0.15% per bar
    volatility = base_vol
    start = datetime(2024, 1, 1)
    rows: list[list[str]] = []

    for i in range(bars):
        ts = start + timedelta(hours=i)

        # Volatility clustering (GARCH-like)
        volatility = 0.85 * volatility + 0.15 * base_vol + rng.gauss(0, 0.0003)
        volatility = max(0.0005, min(volatility, 0.005))

        # Slight mean-reversion toward 32500
        drift = 0.0001 * (32500 - price) / 32500
        ret = drift + rng.gauss(0, volatility)

        # Intra-bar simulation: open -> random walk -> close, track high/low
        open_price = price
        intra = open_price
        high_price = open_price
        low_price = open_price
        steps = 12
        step_vol = volatility / math.sqrt(steps)
        for _ in range(steps):
            intra *= 1 + rng.gauss(ret / steps, step_vol)
            high_price = max(high_price, intra)
            low_price = min(low_price, intra)
        close_price = intra

        # Volume with some randomness (higher on bigger moves)
        move_pct = abs(close_price - open_price) / open_price
        vol_base = 150 + rng.gauss(0, 30)
        vol = max(50, vol_base * (1 + move_pct * 80))

        rows.append([
            ts.strftime("%Y-%m-%d %H:%M:%S"),
            f"{open_price:.2f}",
            f"{high_price:.2f}",
            f"{low_price:.2f}",
            f"{close_price:.2f}",
            f"{vol:.0f}",
        ])

        price = close_price

    return rows


def generate_sample_csv(bars: int = 500, seed: int = 42) -> str:
    """Generate a complete CSV string with header + data rows."""
    header = "timestamp,open,high,low,close,volume"
    rows = generate_sample_ohlcv(bars=bars, seed=seed)
    lines = [header] + [",".join(row) for row in rows]
    return "\n".join(lines) + "\n"
