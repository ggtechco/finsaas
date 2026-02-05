"""Seed the database with sample data."""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from finsaas.core.config import get_settings
from finsaas.data.loader import load_csv_to_db
from finsaas.data.models import Base


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)

    # Create all tables
    Base.metadata.create_all(engine)
    print("Tables created.")

    # Load sample data
    sample_csv = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_ohlcv.csv"
    if sample_csv.exists():
        with Session(engine) as session:
            count = load_csv_to_db(
                session=session,
                filepath=sample_csv,
                ticker="BTCUSDT",
                timeframe="1h",
                exchange="Binance",
            )
        print(f"Loaded {count} bars from sample CSV.")
    else:
        print(f"Sample CSV not found at {sample_csv}")

    print("Database seeded successfully.")


if __name__ == "__main__":
    main()
