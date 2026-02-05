"""CLI commands for data import/export."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("import")
def import_data(
    file: str = typer.Argument(..., help="Path to CSV file"),
    ticker: str = typer.Option(..., "--ticker", "-t", help="Symbol ticker"),
    timeframe: str = typer.Option("1h", "--timeframe", "-tf", help="Timeframe"),
    exchange: str = typer.Option("", "--exchange", "-e", help="Exchange name"),
    timestamp_format: str = typer.Option(
        "%Y-%m-%d %H:%M:%S", "--ts-format", help="Timestamp format"
    ),
) -> None:
    """Import OHLCV data from a CSV file into the database."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from finsaas.core.config import get_settings
    from finsaas.data.loader import load_csv_to_db

    filepath = Path(file)
    if not filepath.exists():
        console.print(f"[red]File not found: {filepath}[/red]")
        raise typer.Exit(1)

    settings = get_settings()
    engine = create_engine(settings.database_url)

    with Session(engine) as session:
        count = load_csv_to_db(
            session=session,
            filepath=filepath,
            ticker=ticker,
            timeframe=timeframe,
            exchange=exchange,
            timestamp_format=timestamp_format,
        )

    console.print(f"[green]Imported {count} bars for {ticker} ({timeframe})[/green]")


@app.command("export")
def export_data(
    ticker: str = typer.Option(..., "--ticker", "-t", help="Symbol ticker"),
    timeframe: str = typer.Option("1h", "--timeframe", "-tf", help="Timeframe"),
    output: str = typer.Option("output.csv", "--output", "-o", help="Output CSV path"),
) -> None:
    """Export OHLCV data from database to CSV."""
    import csv
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from finsaas.core.config import get_settings
    from finsaas.data.repository import OHLCVRepository, SymbolRepository

    settings = get_settings()
    engine = create_engine(settings.database_url)

    with Session(engine) as session:
        symbol_repo = SymbolRepository(session)
        symbol = symbol_repo.get_by_ticker(ticker)
        if not symbol:
            console.print(f"[red]Symbol {ticker} not found[/red]")
            raise typer.Exit(1)

        ohlcv_repo = OHLCVRepository(session)
        bars = ohlcv_repo.get_bars(symbol.id, timeframe)

    with open(output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for bar in bars:
            writer.writerow([
                bar.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                bar.open, bar.high, bar.low, bar.close, bar.volume,
            ])

    console.print(f"[green]Exported {len(bars)} bars to {output}[/green]")
