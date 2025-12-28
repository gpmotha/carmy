"""Week skeleton management commands for Carmy CLI (v2)."""

from datetime import date, timedelta

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from carmy.models.cooking_event import CookingEvent
from carmy.models.cooking_rhythm import CookingRhythm
from carmy.models.database import get_engine, init_db
from carmy.models.meal import Meal
from carmy.models.meal_slot import MealSlot
from carmy.models.month_plan import MonthPlan
from carmy.models.week_skeleton import WeekSkeleton

app = typer.Typer(help="Week skeleton management (v2)")
console = Console()


def get_current_week() -> tuple[int, int]:
    """Get current ISO year and week number."""
    today = date.today()
    iso = today.isocalendar()
    return iso[0], iso[1]


def get_week_dates(year: int, week: int) -> tuple[date, date]:
    """Get start and end dates for ISO week."""
    jan_4 = date(year, 1, 4)
    start_of_week_1 = jan_4 - timedelta(days=jan_4.weekday())
    start_date = start_of_week_1 + timedelta(weeks=week - 1)
    end_date = start_date + timedelta(days=6)
    return start_date, end_date


DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@app.command("list")
def list_weeks(
    year: int = typer.Option(None, "--year", "-y", help="Filter by year"),
    month: int = typer.Option(None, "--month", "-m", help="Filter by month plan"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of weeks to show"),
) -> None:
    """List week skeletons."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        query = select(WeekSkeleton).order_by(
            WeekSkeleton.year.desc(), WeekSkeleton.week_number.desc()
        )

        if year:
            query = query.where(WeekSkeleton.year == year)

        query = query.limit(limit)
        weeks = session.execute(query).scalars().all()

        if not weeks:
            console.print("[yellow]No week skeletons found.[/]")
            return

        table = Table(title="Week Skeletons")
        table.add_column("Year", style="cyan")
        table.add_column("Week", style="cyan")
        table.add_column("Start", style="green")
        table.add_column("End", style="green")
        table.add_column("Status")
        table.add_column("Events", justify="right")
        table.add_column("Slots", justify="right")

        for w in weeks:
            status_color = {
                "skeleton": "yellow",
                "planned": "blue",
                "active": "green",
                "completed": "dim",
            }.get(w.status, "white")

            table.add_row(
                str(w.year),
                f"W{w.week_number}",
                str(w.start_date),
                str(w.end_date),
                f"[{status_color}]{w.status}[/]",
                str(len(w.cooking_events)),
                str(len(w.meal_slots)),
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(weeks)} week(s)[/]")


@app.command("show")
def show_week(
    week: int = typer.Option(None, "--week", "-w", help="Week number"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
) -> None:
    """Show details of a week skeleton."""
    current_year, current_week = get_current_week()

    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        skeleton = session.execute(
            select(WeekSkeleton)
            .where(WeekSkeleton.year == year, WeekSkeleton.week_number == week)
            .options(
                selectinload(WeekSkeleton.cooking_events).selectinload(CookingEvent.meal),
                selectinload(WeekSkeleton.meal_slots).selectinload(MealSlot.meal),
            )
        ).scalar_one_or_none()

        if not skeleton:
            console.print(f"[red]No skeleton found for {year}-W{week}[/]")
            raise typer.Exit(1)

        # Header
        status_color = {
            "skeleton": "yellow",
            "planned": "blue",
            "active": "green",
            "completed": "dim",
        }.get(skeleton.status, "white")

        console.print(Panel(
            f"[bold]Week {skeleton.week_number}, {skeleton.year}[/]\n"
            f"{skeleton.start_date} - {skeleton.end_date}\n"
            f"Status: [{status_color}]{skeleton.status}[/]",
            title="Week Skeleton",
        ))

        # Cooking events
        if skeleton.cooking_events:
            console.print("\n[bold cyan]Cooking Events:[/]")
            events_table = Table(show_header=True, box=None)
            events_table.add_column("Date")
            events_table.add_column("Meal", style="green")
            events_table.add_column("Type")
            events_table.add_column("Effort")
            events_table.add_column("Serves", justify="right")
            events_table.add_column("Made", justify="center")

            for event in sorted(skeleton.cooking_events, key=lambda x: x.cook_date):
                meal_name = event.meal.name if event.meal else f"[dim]Meal #{event.meal_id}[/]"
                day_name = DAY_NAMES[event.cook_date.weekday()]
                made = "[green]Y[/]" if event.was_made else "[dim]?[/]" if event.was_made is None else "[red]N[/]"

                events_table.add_row(
                    f"{day_name} {event.cook_date.day}",
                    meal_name,
                    event.event_type,
                    event.effort_level,
                    f"{event.serves_days}d",
                    made,
                )
            console.print(events_table)
        else:
            console.print("\n[dim]No cooking events[/]")

        # Meal slots
        if skeleton.meal_slots:
            console.print("\n[bold cyan]Meal Slots:[/]")
            slots_table = Table(show_header=True, box=None)
            slots_table.add_column("Date")
            slots_table.add_column("Time")
            slots_table.add_column("Meal", style="green")
            slots_table.add_column("Source")
            slots_table.add_column("Status")

            for slot in sorted(skeleton.meal_slots, key=lambda x: (x.date, x.meal_time)):
                meal_name = slot.meal.name if slot.meal else "-"
                day_name = DAY_NAMES[slot.date.weekday()]
                source_color = {
                    "fresh": "green",
                    "leftover": "yellow",
                    "light": "blue",
                    "eat_out": "magenta",
                    "skip": "dim",
                }.get(slot.source, "white")

                slots_table.add_row(
                    f"{day_name} {slot.date.day}",
                    slot.meal_time,
                    meal_name,
                    f"[{source_color}]{slot.source}[/]",
                    slot.status,
                )
            console.print(slots_table)
        else:
            console.print("\n[dim]No meal slots[/]")


@app.command("create")
def create_week(
    week: int = typer.Option(..., "--week", "-w", help="Week number"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
    month_plan: int = typer.Option(None, "--month-plan", "-mp", help="Link to month plan ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """Create a new week skeleton."""
    current_year, _ = get_current_week()

    if year is None:
        year = current_year

    if week < 1 or week > 53:
        console.print(f"[red]Invalid week:[/] {week}. Must be 1-53.")
        raise typer.Exit(1)

    start_date, end_date = get_week_dates(year, week)

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        existing = session.execute(
            select(WeekSkeleton).where(
                WeekSkeleton.year == year, WeekSkeleton.week_number == week
            )
        ).scalar_one_or_none()

        if existing and not force:
            console.print(f"[yellow]Week skeleton for {year}-W{week} already exists.[/]")
            console.print("Use --force to overwrite.")
            raise typer.Exit(1)

        if existing and force:
            session.delete(existing)
            session.commit()

        skeleton = WeekSkeleton(
            year=year,
            week_number=week,
            start_date=start_date,
            end_date=end_date,
            month_plan_id=month_plan,
            status="skeleton",
        )
        session.add(skeleton)
        session.commit()

        console.print(f"[green]Created week skeleton:[/] {year}-W{week}")
        console.print(f"  {start_date} - {end_date}")


@app.command("materialize")
def materialize_week(
    week: int = typer.Option(None, "--week", "-w", help="Week number"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
    include_lunch: bool = typer.Option(True, "--lunch/--no-lunch", help="Generate lunch slots"),
    include_soup: bool = typer.Option(True, "--soup/--no-soup", help="Generate soup slots"),
) -> None:
    """Materialize a week skeleton into daily meal slots.

    Takes cooking events and generates meal slots for each day,
    including:
    - Fresh meals on cooking days
    - Leftover chains across subsequent days
    - Soup slots (parallel track)
    - Lunch assignments from previous day's leftovers
    - Light meal placeholders for gaps
    """
    from carmy.services.week_materializer import WeekMaterializer

    current_year, current_week = get_current_week()

    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        skeleton = session.execute(
            select(WeekSkeleton)
            .where(WeekSkeleton.year == year, WeekSkeleton.week_number == week)
            .options(
                selectinload(WeekSkeleton.cooking_events).selectinload(CookingEvent.meal),
                selectinload(WeekSkeleton.meal_slots),
            )
        ).scalar_one_or_none()

        if not skeleton:
            console.print(f"[red]No skeleton found for {year}-W{week}[/]")
            raise typer.Exit(1)

        if not skeleton.cooking_events:
            console.print(f"[yellow]No cooking events to materialize for {year}-W{week}[/]")
            console.print("[dim]Add cooking events first.[/]")
            raise typer.Exit(1)

        # Use the WeekMaterializer service
        materializer = WeekMaterializer(session)
        materialized, slots = materializer.materialize_and_save(
            skeleton,
            include_lunch=include_lunch,
            include_soup=include_soup,
        )

        # Display results
        console.print(f"[green]Materialized {year}-W{week}![/]")
        console.print(f"  Created {materialized.slots_created} meal slots from {len(skeleton.cooking_events)} cooking events")

        # Show warnings if any
        if materialized.warnings:
            console.print("\n[yellow]Warnings:[/]")
            for warning in materialized.warnings:
                console.print(f"  - {warning}")

        # Show summary
        summary = materializer.get_week_summary(skeleton)
        console.print("\n[cyan]Summary:[/]")
        console.print(f"  Dinners: {summary['dinners']}  Lunches: {summary['lunches']}")
        console.print(f"  Fresh: {summary['fresh_meals']}  Leftover: {summary['leftover_meals']}  Light: {summary['light_meals']}")
        if summary['soups'] > 0:
            console.print(f"  Soups: {summary['soups']}")

        console.print("\n[dim]Use 'carmy week show' to see the full result.[/]")


@app.command("summary")
def week_summary(
    week: int = typer.Option(None, "--week", "-w", help="Week number"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
) -> None:
    """Show a summary of a week's meal plan."""
    from carmy.services.week_materializer import WeekMaterializer

    current_year, current_week = get_current_week()

    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        skeleton = session.execute(
            select(WeekSkeleton)
            .where(WeekSkeleton.year == year, WeekSkeleton.week_number == week)
            .options(
                selectinload(WeekSkeleton.meal_slots).selectinload(MealSlot.meal),
            )
        ).scalar_one_or_none()

        if not skeleton:
            console.print(f"[red]No skeleton found for {year}-W{week}[/]")
            raise typer.Exit(1)

        if not skeleton.meal_slots:
            console.print(f"[yellow]No meal slots for {year}-W{week}[/]")
            console.print("[dim]Run 'carmy week materialize' first.[/]")
            raise typer.Exit(1)

        materializer = WeekMaterializer(session)
        summary = materializer.get_week_summary(skeleton)

        # Header
        console.print(Panel(
            f"[bold]Week {week}, {year}[/]\n"
            f"{skeleton.start_date} - {skeleton.end_date}",
            title="Week Summary",
        ))

        # Stats table
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", justify="right")

        stats_table.add_row("Total Slots", str(summary['total_slots']))
        stats_table.add_row("Dinners", str(summary['dinners']))
        stats_table.add_row("Lunches", str(summary['lunches']))
        stats_table.add_row("", "")
        stats_table.add_row("Fresh Meals", f"[green]{summary['fresh_meals']}[/]")
        stats_table.add_row("Leftovers", f"[yellow]{summary['leftover_meals']}[/]")
        stats_table.add_row("Light Meals", f"[blue]{summary['light_meals']}[/]")
        if summary['eat_out'] > 0:
            stats_table.add_row("Eat Out", f"[magenta]{summary['eat_out']}[/]")
        if summary['soups'] > 0:
            stats_table.add_row("Soups", str(summary['soups']))

        console.print(stats_table)

        # Day-by-day breakdown
        console.print("\n[bold cyan]Daily Breakdown:[/]")
        for day_str in sorted(summary['by_day'].keys()):
            day_info = summary['by_day'][day_str]
            day_name = day_info['day_name']
            slots = day_info['slots']

            slot_strs = []
            for slot in slots:
                source_color = {
                    "fresh": "green",
                    "leftover": "yellow",
                    "light": "blue",
                    "eat_out": "magenta",
                }.get(slot['source'], "white")

                meal_name = slot['meal_name'] or "[dim]light[/]"
                if slot['leftover_day'] and slot['leftover_day'] > 1:
                    meal_name += f" (day {slot['leftover_day']})"

                slot_strs.append(
                    f"{slot['meal_time']}: [{source_color}]{meal_name}[/]"
                )

            console.print(f"  [cyan]{day_name}[/]: {' | '.join(slot_strs)}")


@app.command("add-event")
def add_cooking_event(
    meal_id: int = typer.Argument(..., help="Meal ID to cook"),
    cook_date: str = typer.Argument(..., help="Cook date (YYYY-MM-DD)"),
    serves_days: int = typer.Option(1, "--serves", "-s", help="How many days this meal feeds (1-7)"),
    effort: str = typer.Option("medium", "--effort", "-e", help="Effort level: none, quick, medium, big"),
    event_type: str = typer.Option("regular", "--type", "-t", help="Event type: big_cook, mid_week, quick, special, regular"),
    week: int = typer.Option(None, "--week", "-w", help="Week number (auto-detected from date)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (auto-detected from date)"),
) -> None:
    """Add a cooking event to a week skeleton."""
    try:
        cook_date_obj = date.fromisoformat(cook_date)
    except ValueError:
        console.print(f"[red]Invalid date format:[/] {cook_date}. Use YYYY-MM-DD.")
        raise typer.Exit(1)

    # Auto-detect week/year from date
    if year is None or week is None:
        iso = cook_date_obj.isocalendar()
        if year is None:
            year = iso[0]
        if week is None:
            week = iso[1]

    if serves_days < 1 or serves_days > 7:
        console.print(f"[red]Invalid serves_days:[/] {serves_days}. Must be 1-7.")
        raise typer.Exit(1)

    valid_efforts = ["none", "quick", "medium", "big"]
    if effort not in valid_efforts:
        console.print(f"[red]Invalid effort:[/] {effort}. Must be one of: {', '.join(valid_efforts)}")
        raise typer.Exit(1)

    valid_types = ["big_cook", "mid_week", "quick", "special", "regular"]
    if event_type not in valid_types:
        console.print(f"[red]Invalid event type:[/] {event_type}. Must be one of: {', '.join(valid_types)}")
        raise typer.Exit(1)

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        # Find or create skeleton
        skeleton = session.execute(
            select(WeekSkeleton).where(
                WeekSkeleton.year == year, WeekSkeleton.week_number == week
            )
        ).scalar_one_or_none()

        if not skeleton:
            # Auto-create skeleton
            start_date, end_date = get_week_dates(year, week)
            skeleton = WeekSkeleton(
                year=year,
                week_number=week,
                start_date=start_date,
                end_date=end_date,
                status="skeleton",
            )
            session.add(skeleton)
            session.commit()
            session.refresh(skeleton)
            console.print(f"[dim]Created week skeleton for {year}-W{week}[/]")

        # Verify meal exists
        meal = session.execute(
            select(Meal).where(Meal.id == meal_id)
        ).scalar_one_or_none()

        if not meal:
            console.print(f"[red]Meal not found:[/] {meal_id}")
            raise typer.Exit(1)

        event = CookingEvent(
            week_skeleton_id=skeleton.id,
            meal_id=meal_id,
            cook_date=cook_date_obj,
            serves_days=serves_days,
            effort_level=effort,
            event_type=event_type,
        )
        session.add(event)
        session.commit()

        day_name = DAY_NAMES[cook_date_obj.weekday()]
        console.print(f"[green]Added cooking event:[/] {meal.name}")
        console.print(f"  Date: {day_name} {cook_date}")
        console.print(f"  Serves: {serves_days} day(s)")
        console.print(f"  Effort: {effort}")


@app.command("rhythm")
def show_rhythm() -> None:
    """Show learned cooking rhythm patterns."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        rhythms = session.execute(
            select(CookingRhythm).order_by(CookingRhythm.day_of_week)
        ).scalars().all()

        if not rhythms:
            console.print("[yellow]No cooking rhythm data found.[/]")
            console.print("[dim]Rhythm is learned from historical cooking patterns.[/]")
            return

        table = Table(title="Cooking Rhythm")
        table.add_column("Day", style="cyan")
        table.add_column("Cook Prob", justify="right")
        table.add_column("Typical Effort")
        table.add_column("Typical Types")
        table.add_column("Confidence", justify="right")

        day_names_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for r in rhythms:
            prob_color = "green" if r.cook_probability > 0.5 else "yellow" if r.cook_probability > 0.2 else "dim"
            types = ", ".join(r.typical_types) if r.typical_types else "-"

            table.add_row(
                day_names_full[r.day_of_week],
                f"[{prob_color}]{r.cook_probability:.0%}[/]",
                r.typical_effort or "-",
                types,
                f"{r.confidence:.0%}",
            )

        console.print(table)
        console.print(f"\n[dim]Last calculated: {rhythms[0].calculated_at if rhythms else 'N/A'}[/]")
