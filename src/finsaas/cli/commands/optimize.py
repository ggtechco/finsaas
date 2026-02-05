"""CLI commands for parameter optimization."""

from __future__ import annotations

from decimal import Decimal

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("run")
def run_optimization(
    strategy: str = typer.Option(..., "--strategy", "-s", help="Strategy name"),
    symbol: str = typer.Option(..., "--symbol", help="Symbol ticker"),
    timeframe: str = typer.Option("1h", "--timeframe", "-tf", help="Timeframe"),
    method: str = typer.Option("grid", "--method", "-m", help="Optimization method: grid, genetic"),
    objective: str = typer.Option("sharpe", "--objective", "-obj", help="Objective: sharpe, sortino, return, max_dd"),
    csv_file: str = typer.Option(None, "--csv", help="CSV data file"),
    capital: float = typer.Option(10000, "--capital", "-c", help="Initial capital"),
    generations: int = typer.Option(50, "--generations", "-g", help="Generations (genetic only)"),
    population: int = typer.Option(50, "--population", help="Population size (genetic only)"),
    workers: int = typer.Option(1, "--workers", "-w", help="Parallel workers"),
    top_n: int = typer.Option(10, "--top", help="Show top N results"),
) -> None:
    """Run parameter optimization for a strategy."""
    from finsaas.core.types import SymbolInfo, Timeframe as TF
    from finsaas.data.feed import CSVFeed
    from finsaas.engine.runner import BacktestConfig
    from finsaas.optimization.optimizer import run_optimization as _run_opt
    from finsaas.strategy.registry import get_strategy

    if not csv_file:
        console.print("[red]Use --csv to provide data.[/red]")
        raise typer.Exit(1)

    feed = CSVFeed(filepath=csv_file, symbol=symbol, timeframe=timeframe)
    config = BacktestConfig(
        symbol_info=SymbolInfo(ticker=symbol),
        timeframe=TF(timeframe),
        initial_capital=Decimal(str(capital)),
    )

    strategy_cls = get_strategy(strategy)

    with console.status("[bold green]Running optimization..."):
        result = _run_opt(
            strategy_cls=strategy_cls,
            feed=feed,
            config=config,
            method=method,
            objective=objective,
            max_workers=workers,
            generations=generations,
            population_size=population,
        )

    # Display results
    console.print(f"\n[bold]Optimization complete: {result.total_trials} trials[/bold]")
    console.print(f"[bold green]Best {objective}: {result.best_value:.4f}[/bold green]")
    console.print(f"Best params: {result.best_params}")

    if result.top_trials:
        table = Table(title=f"Top {min(top_n, len(result.top_trials))} Results")
        table.add_column("#", style="dim")
        table.add_column("Objective", style="cyan")
        table.add_column("Parameters")

        for i, trial in enumerate(result.top_trials[:top_n], 1):
            table.add_row(
                str(i),
                f"{trial.objective_value:.4f}",
                str(trial.parameters),
            )
        console.print(table)
