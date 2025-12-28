"""Analytics commands for Carmy CLI."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy.orm import Session

from carmy.models.database import get_engine, init_db
from carmy.services.analytics import AnalyticsService

app = typer.Typer(help="Analytics and reports")
console = Console()


@app.command("report")
def full_report() -> None:
    """Generate a full analytics report."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        service = AnalyticsService(session)
        report = service.generate_full_report()

        console.print(Panel("[bold]Carmy Analytics Report[/]", subtitle=f"Generated: {report.generated_date}"))

        # Frequency summary
        console.print("\n[bold cyan]Meal Frequency[/]")
        console.print(f"  Total meals in catalog: {report.frequency.total_meals}")
        console.print(f"  Total uses in plans: {report.frequency.total_uses}")
        console.print(f"  Average uses per meal: {report.frequency.average_uses_per_meal:.1f}")
        console.print(f"  Never used meals: {len(report.frequency.never_used)}")

        # Top 5 most used
        console.print("\n  [bold]Top 5 Most Used:[/]")
        for name, count in report.frequency.most_used[:5]:
            console.print(f"    {name}: {count} times")

        # Cuisine distribution
        console.print("\n[bold cyan]Cuisine Distribution[/]")
        for cuisine, count, pct in report.cuisine.top_cuisines[:5]:
            bar = "#" * int(pct / 3)
            console.print(f"  {cuisine:18} {pct:5.1f}% {bar}")

        # Patterns
        console.print("\n[bold cyan]Weekly Averages[/]")
        console.print(f"  Meals per week: {report.patterns.meals_per_week_avg:.1f}")
        console.print(f"  Soups per week: {report.patterns.soups_per_week_avg:.1f}")
        console.print(f"  Main courses per week: {report.patterns.mains_per_week_avg:.1f}")
        console.print(f"  Meat dishes per week: {report.patterns.meat_per_week_avg:.1f}")
        console.print(f"  Vegetarian per week: {report.patterns.vegetarian_per_week_avg:.1f}")

        # Leftovers
        console.print("\n[bold cyan]Leftover Stats[/]")
        console.print(f"  Total leftover entries: {report.leftovers.total_leftovers}")
        console.print(f"  Leftover percentage: {report.leftovers.leftover_percentage:.1f}%")

        if report.leftovers.most_common_leftovers:
            console.print("\n  [bold]Most Common Leftovers:[/]")
            for name, count in report.leftovers.most_common_leftovers[:5]:
                console.print(f"    {name}: {count} times")


@app.command("frequency")
def frequency_report(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of meals to show"),
    show_unused: bool = typer.Option(False, "--unused", "-u", help="Show never-used meals"),
) -> None:
    """Show meal frequency report."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        service = AnalyticsService(session)
        report = service.get_frequency_report(limit=limit)

        console.print(f"\n[bold]Meal Frequency Report[/]")
        console.print(f"Total meals: {report.total_meals} | Total uses: {report.total_uses}")
        console.print(f"Average uses per meal: {report.average_uses_per_meal:.1f}\n")

        # Most used table
        table = Table(title="Most Used Meals")
        table.add_column("#", style="dim", justify="right")
        table.add_column("Meal", style="green")
        table.add_column("Count", justify="right", style="cyan")

        for i, (name, count) in enumerate(report.most_used, 1):
            table.add_row(str(i), name, str(count))

        console.print(table)

        # Never used
        if show_unused and report.never_used:
            console.print(f"\n[yellow]Never Used Meals ({len(report.never_used)}):[/]")
            for name in report.never_used:
                console.print(f"  - {name}")


@app.command("cuisines")
def cuisine_report() -> None:
    """Show cuisine distribution report."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        service = AnalyticsService(session)
        report = service.get_cuisine_report()

        console.print(f"\n[bold]Cuisine Distribution[/]")
        console.print(f"Total meals with cuisine data: {report.total_meals_with_cuisine}\n")

        table = Table(title="Cuisine Breakdown")
        table.add_column("Cuisine", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("%", justify="right")
        table.add_column("Distribution")

        for cuisine, count, pct in report.top_cuisines:
            bar = "#" * int(pct / 2)
            table.add_row(cuisine, str(count), f"{pct:.1f}%", bar)

        console.print(table)


@app.command("types")
def types_report() -> None:
    """Show meal type distribution report."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        service = AnalyticsService(session)
        report = service.get_type_report()

        console.print(f"\n[bold]Meal Type Distribution[/]\n")

        table = Table(title="Type Breakdown")
        table.add_column("Type", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("%", justify="right")
        table.add_column("Distribution")

        for meal_type in sorted(report.distribution.keys(), key=lambda t: report.distribution[t], reverse=True):
            count = report.distribution[meal_type]
            pct = report.percentages[meal_type]
            bar = "#" * int(pct / 2)
            table.add_row(meal_type, str(count), f"{pct:.1f}%", bar)

        console.print(table)


@app.command("leftovers")
def leftover_report() -> None:
    """Show leftover tracking report."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        service = AnalyticsService(session)
        report = service.get_leftover_report()

        console.print(f"\n[bold]Leftover Analysis[/]\n")
        console.print(f"Total meal entries: {report.total_meals}")
        console.print(f"Leftover entries: {report.total_leftovers}")
        console.print(f"Leftover rate: {report.leftover_percentage:.1f}%\n")

        if report.most_common_leftovers:
            table = Table(title="Most Common Leftovers")
            table.add_column("Meal", style="green")
            table.add_column("Times as Leftover", justify="right", style="cyan")

            for name, count in report.most_common_leftovers:
                table.add_row(name, str(count))

            console.print(table)
        else:
            console.print("[dim]No leftover data found.[/]")


@app.command("patterns")
def patterns_report() -> None:
    """Show eating pattern analysis."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        service = AnalyticsService(session)
        report = service.get_pattern_report()

        console.print(f"\n[bold]Eating Patterns Analysis[/]\n")

        console.print("[bold cyan]Weekly Averages:[/]")
        console.print(f"  Meals per week:      {report.meals_per_week_avg:.1f}")
        console.print(f"  Soups per week:      {report.soups_per_week_avg:.1f}")
        console.print(f"  Main courses/week:   {report.mains_per_week_avg:.1f}")
        console.print(f"  Meat dishes/week:    {report.meat_per_week_avg:.1f}")
        console.print(f"  Vegetarian/week:     {report.vegetarian_per_week_avg:.1f}")

        # Show recent trends
        if report.weekly_trends:
            console.print("\n[bold cyan]Recent Weekly Trends:[/]")
            table = Table()
            table.add_column("Week", style="dim")
            table.add_column("Total", justify="right")
            table.add_column("Soups", justify="right")
            table.add_column("Mains", justify="right")
            table.add_column("Meat", justify="right")
            table.add_column("Veg", justify="right")

            for trend in report.weekly_trends[-10:]:
                table.add_row(
                    f"W{trend['week']}/{trend['year']}",
                    str(trend["total"]),
                    str(trend["soups"]),
                    str(trend["mains"]),
                    str(trend["meat"]),
                    str(trend["vegetarian"]),
                )

            console.print(table)


@app.command("trends")
def trends_report(
    weeks: int = typer.Option(12, "--weeks", "-w", help="Number of weeks to analyze"),
) -> None:
    """Show trends over recent weeks."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        service = AnalyticsService(session)
        trends = service.get_trends(weeks=weeks)

        if not trends["weeks"]:
            console.print("[yellow]No trend data available.[/]")
            return

        console.print(f"\n[bold]Trends Over Last {len(trends['weeks'])} Weeks[/]\n")

        # Simple ASCII chart
        console.print("[bold cyan]Meals per Week:[/]")
        max_count = max(trends["meal_counts"]) if trends["meal_counts"] else 1
        for week, count in zip(trends["weeks"], trends["meal_counts"]):
            bar = "#" * int(count / max_count * 30)
            console.print(f"  {week:5} {bar} {count}")

        console.print("\n[bold cyan]Meat Dishes per Week:[/]")
        max_meat = max(trends["meat_counts"]) if trends["meat_counts"] else 1
        for week, count in zip(trends["weeks"], trends["meat_counts"]):
            bar = "#" * int(count / max_meat * 30) if max_meat > 0 else ""
            console.print(f"  {week:5} {bar} {count}")


@app.command("meal-history")
def meal_history(
    meal_id: int = typer.Argument(..., help="Meal ID to show history for"),
) -> None:
    """Show usage history for a specific meal."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        from carmy.models.meal import Meal

        meal = session.get(Meal, meal_id)
        if not meal:
            console.print(f"[red]Meal not found:[/] {meal_id}")
            raise typer.Exit(1)

        service = AnalyticsService(session)
        history = service.get_meal_history(meal_id)

        console.print(f"\n[bold]History for:[/] {meal.name} ({meal.nev})\n")

        if not history:
            console.print("[yellow]This meal has never been used in a plan.[/]")
            return

        table = Table(title=f"Usage History ({len(history)} times)")
        table.add_column("Date", style="cyan")
        table.add_column("Week")
        table.add_column("Leftover", justify="center")

        for entry in history:
            leftover = "L" if entry["is_leftover"] else ""
            table.add_row(
                str(entry["date"]),
                f"W{entry['week']}/{entry['year']}",
                leftover,
            )

        console.print(table)
