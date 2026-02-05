"""Typer CLI entry point for FinSaaS."""

import typer

from finsaas.cli.commands import backtest, data, optimize, pine

app = typer.Typer(
    name="finsaas",
    help="FinSaaS - Backtest & Parameter Optimization Engine",
    no_args_is_help=True,
)

app.add_typer(backtest.app, name="backtest", help="Run backtests")
app.add_typer(data.app, name="data", help="Import/export data")
app.add_typer(optimize.app, name="optimize", help="Parameter optimization")
app.add_typer(pine.app, name="pine", help="Pine Script operations")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
) -> None:
    """Start the web dashboard server."""
    import uvicorn

    typer.echo(f"Starting FinSaaS Dashboard at http://localhost:{port}")
    uvicorn.run(
        "finsaas.web.app:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.callback()
def main() -> None:
    """FinSaaS - Backtest & Parameter Optimization Engine with Pine Script support."""


if __name__ == "__main__":
    app()
