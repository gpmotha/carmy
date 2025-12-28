"""Carmy CLI - A smart weekly meal planner for families."""

import typer
from rich.console import Console

from carmy import __version__
from carmy.cli import analytics, db_cmd, export, import_cmd, meals, month, plans, season, stats, web, week

app = typer.Typer(
    name="carmy",
    help="A smart weekly meal planner for families.",
    no_args_is_help=True,
)
console = Console()

# Register sub-commands
app.add_typer(db_cmd.app, name="db")
app.add_typer(import_cmd.app, name="import")
app.add_typer(meals.app, name="meal")
app.add_typer(plans.app, name="plan")
app.add_typer(season.app, name="season")
app.add_typer(stats.app, name="stats")
app.add_typer(analytics.app, name="analytics")
app.add_typer(export.app, name="export")
app.add_typer(web.app, name="web")
# v2 commands
app.add_typer(month.app, name="month")
app.add_typer(week.app, name="week")


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
        is_eager=True,
    ),
    lang: str = typer.Option(
        "en",
        "--lang",
        "-l",
        help="Output language (en/hu)",
    ),
) -> None:
    """Carmy - Every second counts.

    A smart weekly meal planner that learns from history.
    """
    if version:
        console.print(f"[bold blue]Carmy[/] version {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
