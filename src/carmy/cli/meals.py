"""Meal management commands for Carmy CLI."""

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import select
from sqlalchemy.orm import Session

from carmy.models.database import get_engine, init_db
from carmy.models.meal import Meal

app = typer.Typer(help="Meal catalog management")
console = Console()


@app.command("list")
def list_meals(
    meal_type: str = typer.Option(None, "--type", "-t", help="Filter by meal type (soup, main_course, etc.)"),
    cuisine: str = typer.Option(None, "--cuisine", "-c", help="Filter by cuisine"),
    search: str = typer.Option(None, "--search", "-s", help="Search in meal names"),
    limit: int = typer.Option(50, "--limit", "-n", help="Number of meals to show"),
) -> None:
    """List meals in the catalog."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        query = select(Meal).order_by(Meal.name)

        if meal_type:
            query = query.where(Meal.meal_type == meal_type.lower().replace(" ", "_"))
        if cuisine:
            query = query.where(Meal.cuisine == cuisine.lower().replace(" ", "_"))
        if search:
            query = query.where(
                Meal.name.ilike(f"%{search}%") | Meal.nev.ilike(f"%{search}%")
            )

        query = query.limit(limit)
        meals = session.execute(query).scalars().all()

        if not meals:
            console.print("[yellow]No meals found.[/]")
            return

        table = Table(title="Meals")
        table.add_column("ID", style="dim")
        table.add_column("Név (HU)", style="cyan")
        table.add_column("Name (EN)", style="green")
        table.add_column("Type")
        table.add_column("Cuisine")
        table.add_column("Meat", justify="center")

        for meal in meals:
            meat_icon = "M" if meal.has_meat else ("V" if meal.is_vegetarian else "-")
            table.add_row(
                str(meal.id),
                meal.nev,
                meal.name,
                meal.meal_type,
                meal.cuisine or "-",
                meat_icon,
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(meals)} meal(s)[/]")


@app.command("show")
def show_meal(
    meal_id: int = typer.Argument(..., help="Meal ID to show"),
) -> None:
    """Show details of a specific meal."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        meal = session.get(Meal, meal_id)

        if not meal:
            console.print(f"[red]Meal not found: {meal_id}[/]")
            raise typer.Exit(1)

        console.print(f"\n[bold cyan]{meal.nev}[/] / [bold green]{meal.name}[/]")
        console.print(f"  Type: {meal.meal_type}")
        console.print(f"  Cuisine: {meal.cuisine or 'Not specified'}")
        console.print(f"  Category: {meal.category or 'Not specified'}")

        if meal.calories:
            console.print(f"  Calories: {meal.calories}")
        if meal.prep_time_minutes or meal.cook_time_minutes:
            console.print(f"  Time: {meal.prep_time_minutes}min prep + {meal.cook_time_minutes}min cook")

        console.print(f"  Difficulty: {meal.difficulty}")
        console.print(f"  Seasonality: {meal.seasonality}")

        flags = []
        if meal.is_vegetarian:
            flags.append("[green]Vegetarian[/]")
        if meal.is_vegan:
            flags.append("[green]Vegan[/]")
        if meal.has_meat:
            flags.append("[red]Contains meat[/]")
        if flags:
            console.print(f"  {' | '.join(flags)}")

        if meal.ingredients:
            ing_list = ", ".join(i.ingredient for i in meal.ingredients)
            console.print(f"\n  [bold]Ingredients:[/] {ing_list}")

        if meal.flavor_bases:
            console.print(f"  [bold]Flavor bases:[/] {', '.join(meal.flavor_bases)}")

        if meal.notes:
            console.print(f"\n  [dim]Notes: {meal.notes}[/]")

        # Show usage stats
        usage_count = len(meal.plan_meals)
        if usage_count:
            console.print(f"\n  [dim]Used in {usage_count} weekly plan(s)[/]")


@app.command("types")
def list_types() -> None:
    """Show available meal types and their counts."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        from sqlalchemy import func

        results = session.execute(
            select(Meal.meal_type, func.count(Meal.id))
            .group_by(Meal.meal_type)
            .order_by(func.count(Meal.id).desc())
        ).all()

        table = Table(title="Meal Types")
        table.add_column("Type", style="cyan")
        table.add_column("Count", justify="right", style="green")

        for meal_type, count in results:
            table.add_row(meal_type, str(count))

        console.print(table)


@app.command("cuisines")
def list_cuisines() -> None:
    """Show available cuisines and their counts."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        from sqlalchemy import func

        results = session.execute(
            select(Meal.cuisine, func.count(Meal.id))
            .where(Meal.cuisine.isnot(None))
            .group_by(Meal.cuisine)
            .order_by(func.count(Meal.id).desc())
        ).all()

        table = Table(title="Cuisines")
        table.add_column("Cuisine", style="cyan")
        table.add_column("Count", justify="right", style="green")

        for cuisine, count in results:
            table.add_row(cuisine, str(count))

        console.print(table)
