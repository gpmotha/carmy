"""Database management commands for Carmy CLI."""

from pathlib import Path

import typer
from rich.console import Console

from carmy.models.database import get_database_path, get_engine, init_db
from carmy.migrations.runner import run_migrations

app = typer.Typer(help="Database management commands")
console = Console()


@app.command("init")
def db_init() -> None:
    """Initialize the database.

    Creates all tables in the database. Safe to run multiple times.
    """
    db_path = get_database_path()
    console.print(f"\n[bold blue]Initializing database at:[/] {db_path}")

    init_db()

    console.print("[bold green]Database initialized successfully![/]")


@app.command("reset")
def db_reset(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Reset the database.

    Drops all tables and recreates them. All data will be lost!
    """
    db_path = get_database_path()

    if not force:
        confirm = typer.confirm(
            f"This will DELETE all data in {db_path}. Are you sure?"
        )
        if not confirm:
            console.print("[yellow]Aborted.[/]")
            raise typer.Exit(0)

    console.print(f"\n[bold red]Resetting database at:[/] {db_path}")

    # Delete the database file if it exists
    if db_path.exists():
        db_path.unlink()
        console.print("[yellow]Deleted existing database.[/]")

    # Recreate
    init_db()
    console.print("[bold green]Database reset complete![/]")


@app.command("info")
def db_info() -> None:
    """Show database information."""
    from sqlalchemy import inspect, text
    from sqlalchemy.orm import Session

    db_path = get_database_path()
    console.print(f"\n[bold blue]Database:[/] {db_path}")
    console.print(f"[bold blue]Exists:[/] {db_path.exists()}")

    if not db_path.exists():
        return

    engine = get_engine()
    inspector = inspect(engine)

    console.print("\n[bold]Tables:[/]")
    for table_name in inspector.get_table_names():
        with Session(engine) as session:
            count = session.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            ).scalar()
        console.print(f"  - {table_name}: {count} rows")


@app.command("migrate")
def db_migrate() -> None:
    """Run pending database migrations.

    Applies any unapplied migrations to update the database schema.
    """
    console.print("\n[bold blue]Running database migrations...[/]")

    applied = run_migrations()

    if applied:
        console.print(f"\n[bold green]Applied {len(applied)} migration(s):[/]")
        for name in applied:
            console.print(f"  - {name}")
    else:
        console.print("[yellow]No pending migrations.[/]")
