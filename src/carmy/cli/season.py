"""Seasonality commands for Carmy CLI."""

from datetime import date

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import select
from sqlalchemy.orm import Session

from carmy.models.database import get_engine, init_db
from carmy.models.meal import Meal
from carmy.services.seasonality import SeasonalityService, get_current_season

app = typer.Typer(help="Seasonality information and meal scoring")
console = Console()


@app.command("now")
def show_current_season() -> None:
    """Show current season and recommended ingredients."""
    season = get_current_season()
    service = SeasonalityService()
    suggestions = service.suggest_for_season(season)

    console.print(f"\n[bold]Current Season:[/] [cyan]{season.title()}[/]\n")

    if suggestions.get("vegetables"):
        console.print("[bold green]Vegetables in season:[/]")
        console.print(f"  {', '.join(suggestions['vegetables'])}")

    if suggestions.get("fruits"):
        console.print("\n[bold green]Fruits in season:[/]")
        console.print(f"  {', '.join(suggestions['fruits'])}")

    if suggestions.get("herbs"):
        console.print("\n[bold green]Herbs:[/]")
        console.print(f"  {', '.join(suggestions['herbs'])}")


@app.command("ingredients")
def show_seasonal_ingredients(
    season: str = typer.Argument(None, help="Season (spring, summer, autumn, winter)"),
) -> None:
    """Show seasonal ingredients for a specific season."""
    if season is None:
        season = get_current_season()

    valid_seasons = ["spring", "summer", "autumn", "winter"]
    if season.lower() not in valid_seasons:
        console.print(f"[red]Invalid season:[/] {season}")
        console.print(f"Valid seasons: {', '.join(valid_seasons)}")
        raise typer.Exit(1)

    season = season.lower()
    service = SeasonalityService()
    suggestions = service.suggest_for_season(season)

    console.print(f"\n[bold]{season.title()} Ingredients[/]\n")

    table = Table()
    table.add_column("Category", style="cyan")
    table.add_column("Ingredients", style="green")

    if suggestions.get("vegetables"):
        table.add_row("Vegetables", ", ".join(suggestions["vegetables"]))
    if suggestions.get("fruits"):
        table.add_row("Fruits", ", ".join(suggestions["fruits"]))
    if suggestions.get("herbs"):
        table.add_row("Herbs", ", ".join(suggestions["herbs"]))

    console.print(table)


@app.command("meals")
def show_seasonal_meals(
    season: str = typer.Argument(None, help="Season to check (defaults to current)"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of meals to show"),
    meal_type: str = typer.Option(None, "--type", "-t", help="Filter by meal type"),
) -> None:
    """Show meals ranked by seasonality score."""
    if season is None:
        season = get_current_season()

    valid_seasons = ["spring", "summer", "autumn", "winter"]
    if season.lower() not in valid_seasons:
        console.print(f"[red]Invalid season:[/] {season}")
        raise typer.Exit(1)

    season = season.lower()

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        query = select(Meal)
        if meal_type:
            query = query.where(Meal.meal_type == meal_type.lower().replace(" ", "_"))

        meals = session.execute(query).scalars().all()

        service = SeasonalityService()
        scores = service.score_meals(list(meals), season)[:limit]

        console.print(f"\n[bold]Meals for {season.title()}[/]\n")

        table = Table()
        table.add_column("Name", style="green")
        table.add_column("Type")
        table.add_column("Score", justify="right")
        table.add_column("Rating", style="cyan")
        table.add_column("Seasonal Ingredients")

        for score in scores:
            score_str = f"{score.score:.1%}"
            matching = ", ".join(score.matching_ingredients) if score.matching_ingredients else "-"

            table.add_row(
                score.meal_name,
                next((m.meal_type for m in meals if m.id == score.meal_id), "-"),
                score_str,
                score.rating,
                matching,
            )

        console.print(table)


@app.command("score")
def score_meal(
    meal_id: int = typer.Argument(..., help="Meal ID to score"),
    season: str = typer.Option(None, "--season", "-s", help="Season (defaults to current)"),
) -> None:
    """Score a specific meal for seasonality."""
    if season is None:
        season = get_current_season()

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        meal = session.get(Meal, meal_id)

        if not meal:
            console.print(f"[red]Meal not found:[/] {meal_id}")
            raise typer.Exit(1)

        service = SeasonalityService()
        score = service.score_meal(meal, season)

        console.print(f"\n[bold]{meal.name}[/] ({meal.nev})")
        console.print(f"  Season: [cyan]{season.title()}[/]")
        console.print(f"  Score: [bold]{score.score:.1%}[/] ({score.rating})")

        if score.matching_ingredients:
            console.print(f"  [green]Seasonal ingredients:[/] {', '.join(score.matching_ingredients)}")

        if score.off_season_ingredients:
            console.print(f"  [yellow]Off-season ingredients:[/] {', '.join(score.off_season_ingredients)}")

        # Show score for all seasons
        console.print("\n[dim]Scores by season:[/]")
        for s in ["spring", "summer", "autumn", "winter"]:
            s_score = service.score_meal(meal, s)
            indicator = " <--" if s == season else ""
            console.print(f"  {s.title():8} {s_score.score:.0%}{indicator}")
