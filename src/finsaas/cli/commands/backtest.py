"""CLI command for running backtests."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("run")
def run_backtest(
    strategy: str = typer.Option(..., "--strategy", "-s", help="Strategy name"),
    symbol: str = typer.Option(..., "--symbol", help="Symbol ticker (e.g., BTCUSDT)"),
    timeframe: str = typer.Option("1h", "--timeframe", "-tf", help="Timeframe"),
    start: str = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    capital: float = typer.Option(10000, "--capital", "-c", help="Initial capital"),
    csv_file: str = typer.Option(None, "--csv", help="CSV data file (alternative to DB)"),
    output: str = typer.Option("text", "--output", "-o", help="Output format: text, json"),
    params: list[str] = typer.Option([], "--param", "-p", help="Strategy params (key=value)"),
) -> None:
    """Run a backtest with the given strategy and data."""
    from datetime import datetime

    from finsaas.analytics.report import generate_json_report, generate_text_report
    from finsaas.core.types import SymbolInfo, Timeframe as TF
    from finsaas.data.feed import CSVFeed, InMemoryFeed
    from finsaas.engine.runner import BacktestConfig, BacktestRunner
    from finsaas.strategy.registry import create_strategy

    # Parse parameters
    parsed_params: dict[str, object] = {}
    for p in params:
        key, _, value = p.partition("=")
        try:
            parsed_params[key] = int(value)
        except ValueError:
            try:
                parsed_params[key] = float(value)
            except ValueError:
                parsed_params[key] = value

    # Create strategy
    strat = create_strategy(strategy, **parsed_params)

    # Create data feed
    if csv_file:
        feed = CSVFeed(filepath=csv_file, symbol=symbol, timeframe=timeframe)
    else:
        console.print("[red]Database feed not configured. Use --csv to provide data.[/red]")
        raise typer.Exit(1)

    # Create config
    config = BacktestConfig(
        symbol_info=SymbolInfo(ticker=symbol),
        timeframe=TF(timeframe),
        initial_capital=Decimal(str(capital)),
    )

    # Run backtest
    with console.status("[bold green]Running backtest..."):
        runner = BacktestRunner(feed, config)
        result = runner.run(strat)

    # Output
    if output == "json":
        console.print(generate_json_report(result))
    else:
        console.print(generate_text_report(result))
