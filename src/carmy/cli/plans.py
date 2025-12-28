"""Plan management commands for Carmy CLI."""

from datetime import date, timedelta

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import select
from sqlalchemy.orm import Session

from carmy.models.database import get_engine, init_db
from carmy.models.plan import WeeklyPlan
from carmy.services.generator import GeneratorConfig, PlanGenerator
from carmy.services.rules_engine import RulesEngine, RuleSeverity

app = typer.Typer(help="Weekly plan management")
console = Console()


def get_current_week() -> tuple[int, int]:
    """Get current ISO year and week number."""
    today = date.today()
    iso = today.isocalendar()
    return iso[0], iso[1]


@app.command("list")
def list_plans(
    year: int = typer.Option(None, "--year", "-y", help="Filter by year"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of plans to show"),
) -> None:
    """List weekly plans."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        query = select(WeeklyPlan).order_by(
            WeeklyPlan.year.desc(), WeeklyPlan.week_number.desc()
        )

        if year:
            query = query.where(WeeklyPlan.year == year)

        query = query.limit(limit)
        plans = session.execute(query).scalars().all()

        if not plans:
            console.print("[yellow]No plans found.[/]")
            return

        table = Table(title="Weekly Plans")
        table.add_column("Year", style="cyan")
        table.add_column("Week", style="cyan")
        table.add_column("Start Date", style="green")
        table.add_column("Meals", justify="right")
        table.add_column("Soups", justify="right")
        table.add_column("Mains", justify="right")

        for plan in plans:
            meals = [pm for pm in plan.plan_meals if pm.meal]
            soups = [pm for pm in meals if pm.meal.meal_type == "soup"]
            mains = [pm for pm in meals if pm.meal.meal_type in ("main_course", "pasta", "dinner")]

            table.add_row(
                str(plan.year),
                str(plan.week_number),
                str(plan.start_date),
                str(len(meals)),
                str(len(soups)),
                str(len(mains)),
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(plans)} plan(s)[/]")


@app.command("show")
def show_plan(
    week: int = typer.Option(..., "--week", "-w", help="Week number"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
) -> None:
    """Show details of a specific weekly plan."""
    if year is None:
        year = get_current_week()[0]

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = session.execute(
            select(WeeklyPlan).where(
                WeeklyPlan.year == year, WeeklyPlan.week_number == week
            )
        ).scalar_one_or_none()

        if not plan:
            console.print(f"[red]No plan found for week {week}, {year}[/]")
            raise typer.Exit(1)

        # Header
        console.print(
            Panel(
                f"[bold]Week {plan.week_number}, {plan.year}[/]\n"
                f"Starting: {plan.start_date}",
                title="Weekly Plan",
            )
        )

        # Meals table
        table = Table(title="Meals")
        table.add_column("Név (HU)", style="cyan")
        table.add_column("Name (EN)", style="green")
        table.add_column("Type")
        table.add_column("Cuisine")
        table.add_column("Leftover", justify="center")

        for pm in plan.plan_meals:
            if pm.meal:
                leftover = "L" if pm.is_leftover else ""
                table.add_row(
                    pm.meal.nev,
                    pm.meal.name,
                    pm.meal.meal_type,
                    pm.meal.cuisine or "-",
                    leftover,
                )

        console.print(table)

        # Quick stats
        meals = [pm.meal for pm in plan.plan_meals if pm.meal]
        unique_meals = {m.id: m for m in meals}.values()
        soups = [m for m in unique_meals if m.meal_type == "soup"]
        mains = [m for m in unique_meals if m.meal_type in ("main_course", "pasta", "dinner")]

        console.print(f"\n[dim]Total: {len(meals)} meals ({len(soups)} soups, {len(mains)} mains)[/]")


@app.command("validate")
def validate_plan(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    all_plans: bool = typer.Option(False, "--all", "-a", help="Validate all plans"),
) -> None:
    """Validate a weekly plan against planning rules.

    Checks:
    - Weekly quotas (2 soups, 4 main courses)
    - Taste diversity (no flavor conflicts)
    - Meat limit (max 3 meat dishes)
    - Duplicate detection
    - Cuisine rotation
    """
    current_year, current_week = get_current_week()
    if year is None:
        year = current_year
    if week is None and not all_plans:
        week = current_week

    init_db()
    engine = get_engine()
    rules = RulesEngine()

    with Session(engine) as session:
        if all_plans:
            plans = session.execute(
                select(WeeklyPlan).order_by(WeeklyPlan.year, WeeklyPlan.week_number)
            ).scalars().all()
        else:
            plan = session.execute(
                select(WeeklyPlan).where(
                    WeeklyPlan.year == year, WeeklyPlan.week_number == week
                )
            ).scalar_one_or_none()

            if not plan:
                console.print(f"[red]No plan found for week {week}, {year}[/]")
                raise typer.Exit(1)

            plans = [plan]

        total_errors = 0
        total_warnings = 0

        for plan in plans:
            result = rules.validate(plan)

            if result.violations or not all_plans:
                console.print(f"\n[bold]Week {plan.week_number}, {plan.year}[/]")

                # Show stats
                stats = result.stats
                console.print(
                    f"  Meals: {stats['unique_meals']} unique "
                    f"({stats['soups']} soups, {stats['main_courses']} mains, "
                    f"{stats['meat_dishes']} with meat)"
                )

                if result.violations:
                    for violation in result.violations:
                        color = {
                            RuleSeverity.ERROR: "red",
                            RuleSeverity.WARNING: "yellow",
                            RuleSeverity.INFO: "blue",
                        }[violation.severity]
                        console.print(f"  [{color}]{violation}[/]")

                    total_errors += result.error_count
                    total_warnings += result.warning_count
                else:
                    console.print("  [green]OK - All rules passed[/]")

        # Summary for multiple plans
        if all_plans and len(plans) > 1:
            console.print(f"\n[bold]Summary:[/] {len(plans)} plans validated")
            if total_errors or total_warnings:
                console.print(f"  [red]{total_errors} errors[/], [yellow]{total_warnings} warnings[/]")
            else:
                console.print("  [green]All plans valid![/]")


def get_week_start(year: int, week: int) -> date:
    """Get the Monday of a given ISO week."""
    jan_4 = date(year, 1, 4)
    start_of_week_1 = jan_4 - timedelta(days=jan_4.weekday())
    return start_of_week_1 + timedelta(weeks=week - 1)


@app.command("generate")
def generate_plan(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to next week)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    save: bool = typer.Option(False, "--save", "-s", help="Save the generated plan"),
    randomness: float = typer.Option(0.3, "--randomness", "-r", help="Randomness level (0-1)"),
) -> None:
    """Generate a weekly plan suggestion.

    Creates a plan with 2 soups and 4 main courses, respecting:
    - Recently used meals are avoided
    - No flavor conflicts (e.g., broccoli soup + broccoli pasta)
    - Maximum 3 meat dishes
    - Cuisine rotation
    """
    current_year, current_week = get_current_week()

    if year is None:
        year = current_year
    if week is None:
        # Default to next week
        week = current_week + 1
        if week > 52:
            week = 1
            year += 1

    start_date = get_week_start(year, week)

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        # Check if plan already exists
        existing = session.execute(
            select(WeeklyPlan).where(
                WeeklyPlan.year == year, WeeklyPlan.week_number == week
            )
        ).scalar_one_or_none()

        if existing:
            console.print(f"[yellow]Plan for week {week}, {year} already exists.[/]")
            console.print("Use [bold]carmy plan show[/] to view it.")
            raise typer.Exit(1)

        config = GeneratorConfig(randomness=randomness)
        generator = PlanGenerator(session, config)

        plan = generator.generate(year, week, start_date)

        console.print(f"\n[bold]Generating plan for Week {week}, {year}[/]")
        console.print(f"Starting: {start_date} | Season: [cyan]{plan.season.title()}[/]\n")

        # Display soups
        console.print("[bold cyan]Soups:[/]")
        for i, soup in enumerate(plan.soups, 1):
            cuisine = f" ({soup.cuisine})" if soup.cuisine else ""
            console.print(f"  {i}. {soup.name}{cuisine}")

        # Display main courses
        console.print("\n[bold cyan]Main Courses:[/]")
        for i, main in enumerate(plan.main_courses, 1):
            meat = " [M]" if main.has_meat else ""
            cuisine = f" ({main.cuisine})" if main.cuisine else ""
            console.print(f"  {i}. {main.name}{cuisine}{meat}")

        # Show validation
        if plan.validation:
            console.print("\n[bold]Validation:[/]")
            if plan.validation.is_valid and not plan.validation.violations:
                console.print("  [green]OK - All rules passed[/]")
            else:
                for v in plan.validation.violations:
                    color = {
                        RuleSeverity.ERROR: "red",
                        RuleSeverity.WARNING: "yellow",
                        RuleSeverity.INFO: "blue",
                    }[v.severity]
                    console.print(f"  [{color}]{v}[/]")

        # Save if requested
        if save:
            try:
                saved = generator.save_plan(plan)
                console.print(f"\n[green]Plan saved![/] ID: {saved.id}")
            except ValueError as e:
                console.print(f"\n[red]Could not save:[/] {e}")
        else:
            console.print("\n[dim]Use --save to save this plan[/]")


@app.command("suggest")
def suggest_meals(
    meal_type: str = typer.Argument(..., help="Type of meal to suggest (soup, main)"),
    count: int = typer.Option(5, "--count", "-n", help="Number of suggestions"),
) -> None:
    """Suggest meals of a specific type for rotation.

    Shows underused meals that would be good to include in upcoming plans.
    """
    init_db()
    engine = get_engine()

    # Normalize meal type
    type_map = {
        "soup": "soup",
        "soups": "soup",
        "main": "main_course",
        "mains": "main_course",
        "main_course": "main_course",
        "pasta": "pasta",
    }

    normalized_type = type_map.get(meal_type.lower())
    if not normalized_type:
        console.print(f"[red]Unknown meal type:[/] {meal_type}")
        console.print("Valid types: soup, main, pasta")
        raise typer.Exit(1)

    with Session(engine) as session:
        from carmy.services.analyzer import HistoricalAnalyzer

        analyzer = HistoricalAnalyzer(session)
        candidates = analyzer.get_candidates_for_type(
            normalized_type,
            exclude_recent_weeks=2,
        )[:count]

        if not candidates:
            console.print(f"[yellow]No {meal_type} suggestions available.[/]")
            return

        table = Table(title=f"Suggested {meal_type.title()}s")
        table.add_column("Name", style="green")
        table.add_column("Cuisine")
        table.add_column("Uses", justify="right")
        table.add_column("Last Used")

        for stat in candidates:
            if stat.weeks_since_last_use is None:
                last_used = "[dim]Never[/]"
            elif stat.weeks_since_last_use == 0:
                last_used = "This week"
            else:
                last_used = f"{stat.weeks_since_last_use}w ago"

            table.add_row(
                stat.name,
                stat.cuisine or "-",
                str(stat.total_count),
                last_used,
            )

        console.print(table)
