"""CLI commands for Pine Script operations."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("parse")
def parse_pine(
    file: str = typer.Argument(..., help="Path to Pine Script file"),
    output: str = typer.Option(None, "--output", "-o", help="Output Python file path"),
    show_ast: bool = typer.Option(False, "--ast", help="Show AST instead of Python code"),
) -> None:
    """Parse a Pine Script file and convert to Python strategy."""
    filepath = Path(file)
    if not filepath.exists():
        console.print(f"[red]File not found: {filepath}[/red]")
        raise typer.Exit(1)

    source = filepath.read_text()

    from finsaas.pine.parser import PineParser
    from finsaas.pine.transpiler import PineTranspiler

    parser = PineParser()
    ast = parser.parse(source)

    if show_ast:
        console.print(ast.pretty())
        return

    transpiler = PineTranspiler()
    python_code = transpiler.transpile(ast)

    if output:
        Path(output).write_text(python_code)
        console.print(f"[green]Python strategy written to {output}[/green]")
    else:
        console.print(python_code)


@app.command("validate")
def validate_pine(
    file: str = typer.Argument(..., help="Path to Pine Script file"),
) -> None:
    """Validate a Pine Script file for syntax and semantic errors."""
    filepath = Path(file)
    if not filepath.exists():
        console.print(f"[red]File not found: {filepath}[/red]")
        raise typer.Exit(1)

    source = filepath.read_text()

    from finsaas.pine.parser import PineParser
    from finsaas.pine.semantic import SemanticAnalyzer

    try:
        parser = PineParser()
        ast = parser.parse(source)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        console.print("[green]Pine Script is valid.[/green]")
    except Exception as e:
        console.print(f"[red]Validation error: {e}[/red]")
        raise typer.Exit(1)
