"""Statistics commands for Carmy CLI."""

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy.orm import Session

from carmy.models.database import get_engine, init_db
from carmy.services.analyzer import HistoricalAnalyzer

app = typer.Typer(help="Statistics and analytics")
console = Console()


@app.command("frequency")
def show_frequency(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of meals to show"),
    meal_type: str = typer.Option(None, "--type", "-t", help="Filter by meal type"),
) -> None:
    """Show most frequently used meals."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        analyzer = HistoricalAnalyzer(session)
        stats = analyzer.get_meal_frequency(limit=100)

        if meal_type:
            stats = [s for s in stats if s.meal_type == meal_type.lower().replace(" ", "_")]

        stats = stats[:limit]

        if not stats:
            console.print("[yellow]No meal data found.[/]")
            return

        table = Table(title="Most Used Meals")
        table.add_column("#", style="dim", justify="right")
        table.add_column("Name", style="green")
        table.add_column("Type")
        table.add_column("Cuisine")
        table.add_column("Count", justify="right", style="cyan")
        table.add_column("Last Used")

        for i, stat in enumerate(stats, 1):
            last_used = f"W{stat.last_used_week}/{stat.last_used_year}" if stat.last_used_week else "Never"
            table.add_row(
                str(i),
                stat.name,
                stat.meal_type,
                stat.cuisine or "-",
                str(stat.total_count),
                last_used,
            )

        console.print(table)


@app.command("recent")
def show_recent(
    weeks: int = typer.Option(4, "--weeks", "-w", help="Number of weeks to look back"),
) -> None:
    """Show recently used meals."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        analyzer = HistoricalAnalyzer(session)
        stats = analyzer.get_recent_meals(weeks=weeks)

        if not stats:
            console.print(f"[yellow]No meals used in the last {weeks} weeks.[/]")
            return

        # Sort by recency
        stats = sorted(
            stats,
            key=lambda s: (s.last_used_year or 0, s.last_used_week or 0),
            reverse=True,
        )

        table = Table(title=f"Meals Used in Last {weeks} Weeks")
        table.add_column("Name", style="green")
        table.add_column("Type")
        table.add_column("Last Used", style="cyan")
        table.add_column("Weeks Ago", justify="right")

        for stat in stats:
            last_used = f"W{stat.last_used_week}/{stat.last_used_year}"
            weeks_ago = str(stat.weeks_since_last_use) if stat.weeks_since_last_use else "-"
            table.add_row(
                stat.name,
                stat.meal_type,
                last_used,
                weeks_ago,
            )

        console.print(table)
        console.print(f"\n[dim]{len(stats)} meal(s) used recently[/]")


@app.command("underused")
def show_underused(
    min_gap: int = typer.Option(4, "--gap", "-g", help="Minimum weeks since last use"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of meals to show"),
) -> None:
    """Show meals that haven't been used recently (good for rotation)."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        analyzer = HistoricalAnalyzer(session)
        stats = analyzer.get_underused_meals(min_gap_weeks=min_gap)

        # Sort: never used first, then by weeks since use
        stats = sorted(
            stats,
            key=lambda s: (
                0 if s.weeks_since_last_use is None else 1,
                -(s.weeks_since_last_use or 999),
            ),
        )[:limit]

        if not stats:
            console.print("[yellow]No underused meals found.[/]")
            return

        table = Table(title=f"Underused Meals (>{min_gap} weeks)")
        table.add_column("Name", style="green")
        table.add_column("Type")
        table.add_column("Cuisine")
        table.add_column("Total Uses", justify="right")
        table.add_column("Last Used")

        for stat in stats:
            if stat.weeks_since_last_use is None:
                last_used = "[dim]Never[/]"
            else:
                last_used = f"{stat.weeks_since_last_use} weeks ago"

            table.add_row(
                stat.name,
                stat.meal_type,
                stat.cuisine or "-",
                str(stat.total_count),
                last_used,
            )

        console.print(table)
        console.print(f"\n[dim]{len(stats)} underused meal(s)[/]")


@app.command("overview")
def show_overview() -> None:
    """Show overall statistics and analysis."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        analyzer = HistoricalAnalyzer(session)
        result = analyzer.analyze()

        console.print("\n[bold]Carmy Statistics Overview[/]\n")

        console.print(f"  Total meals in catalog: [cyan]{result.total_meals}[/]")
        console.print(f"  Total weekly plans: [cyan]{result.total_plans}[/]")
        console.print(f"  Never used meals: [yellow]{len(result.never_used)}[/]")

        # Cuisine distribution
        console.print("\n[bold]Cuisine Distribution (in plans):[/]")
        for cuisine, count in list(result.cuisine_distribution.items())[:8]:
            bar = "#" * min(count // 5, 30)
            console.print(f"  {cuisine:20} {count:4} {bar}")

        # Type distribution
        console.print("\n[bold]Meal Type Distribution (in plans):[/]")
        for meal_type, count in list(result.type_distribution.items())[:8]:
            bar = "#" * min(count // 5, 30)
            console.print(f"  {meal_type:20} {count:4} {bar}")

        # Top 5 most used
        console.print("\n[bold]Top 5 Most Used:[/]")
        for stat in result.most_used[:5]:
            console.print(f"  {stat.name}: {stat.total_count} times")
