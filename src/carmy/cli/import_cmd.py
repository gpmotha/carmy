"""Import commands for Carmy CLI."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from carmy.models.database import get_engine, init_db
from carmy.utils.importers import HistoricalDBImporter, XLSXImporter
from sqlalchemy.orm import Session

app = typer.Typer(help="Import data from various sources")
console = Console()


@app.command("history")
def import_history(
    file_path: Path = typer.Argument(
        ...,
        help="Path to Meal_planner.xlsx file",
        exists=True,
        readable=True,
    ),
) -> None:
    """Import historical meal plan data from XLSX file.

    Imports meals and weekly plans from the historical Meal_planner.xlsx file.
    Creates meals in the catalog and assigns them to weekly plans based on the data.
    """
    console.print(f"\n[bold blue]Importing historical data from:[/] {file_path}")

    # Initialize database
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        importer = XLSXImporter(session)

        try:
            stats = importer.import_history(file_path)

            # Display results
            console.print("\n[bold green]Import completed successfully![/]\n")

            table = Table(title="Import Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="green", justify="right")

            table.add_row("Meals created", str(stats["meals_created"]))
            table.add_row("Meals updated", str(stats["meals_updated"]))
            table.add_row("Weekly plans created", str(stats["plans_created"]))
            table.add_row("Plan meals created", str(stats["plan_meals_created"]))
            table.add_row("Rows skipped", str(stats["skipped"]))

            console.print(table)

        except FileNotFoundError as e:
            console.print(f"[bold red]Error:[/] {e}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]Import failed:[/] {e}")
            raise typer.Exit(1)


@app.command("meals")
def import_meals(
    file_path: Path = typer.Argument(
        ...,
        help="Path to meals file (CSV, JSON, or XLSX)",
        exists=True,
        readable=True,
    ),
) -> None:
    """Import meals from CSV, JSON, or XLSX file."""
    console.print(f"\n[bold blue]Importing meals from:[/] {file_path}")

    suffix = file_path.suffix.lower()
    if suffix not in [".csv", ".json", ".xlsx"]:
        console.print(f"[bold red]Error:[/] Unsupported file format: {suffix}")
        raise typer.Exit(1)

    console.print("[yellow]Meal import from CSV/JSON not yet implemented.[/]")
    console.print("Use [bold]carmy import history[/] for XLSX historical data.")


@app.command("historical-db")
def import_historical_db(
    db_path: Path = typer.Argument(
        ...,
        help="Path to carmy_historical.db SQLite database",
        exists=True,
        readable=True,
    ),
) -> None:
    """Import historical meal data from carmy_historical.db.

    Imports meals and weekly plans from the historical SQLite database.
    Creates meals in the catalog and assigns them to weekly plans.

    Example:
        carmy import historical-db data/historical/carmy_historical.db
    """
    console.print(f"\n[bold blue]Importing historical data from:[/] {db_path}")

    # Initialize database
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        importer = HistoricalDBImporter(session)

        try:
            stats = importer.import_from_db(db_path)

            # Display results
            console.print("\n[bold green]Import completed successfully![/]\n")

            table = Table(title="Import Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="green", justify="right")

            table.add_row("Meals created", str(stats["meals_created"]))
            table.add_row("Meals skipped (existing)", str(stats["meals_skipped"]))
            table.add_row("Weekly plans created", str(stats["plans_created"]))
            table.add_row("Weekly plans skipped (existing)", str(stats["plans_skipped"]))
            table.add_row("Plan meals created", str(stats["plan_meals_created"]))
            table.add_row("Plan meals skipped", str(stats["plan_meals_skipped"]))

            console.print(table)

        except FileNotFoundError as e:
            console.print(f"[bold red]Error:[/] {e}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]Import failed:[/] {e}")
            import traceback
            traceback.print_exc()
            raise typer.Exit(1)
