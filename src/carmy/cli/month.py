"""Month planning commands for Carmy CLI (v2)."""

from datetime import date

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import select
from sqlalchemy.orm import Session

from carmy.models.database import get_engine, init_db
from carmy.models.month_plan import MonthPlan, SpecialDate, get_season_for_month

app = typer.Typer(help="Month plan management (v2)")
console = Console()


def get_current_month() -> tuple[int, int]:
    """Get current year and month."""
    today = date.today()
    return today.year, today.month


MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


@app.command("list")
def list_months(
    year: int = typer.Option(None, "--year", "-y", help="Filter by year"),
    limit: int = typer.Option(12, "--limit", "-n", help="Number of plans to show"),
) -> None:
    """List month plans."""
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        query = select(MonthPlan).order_by(
            MonthPlan.year.desc(), MonthPlan.month.desc()
        )

        if year:
            query = query.where(MonthPlan.year == year)

        query = query.limit(limit)
        plans = session.execute(query).scalars().all()

        if not plans:
            console.print("[yellow]No month plans found.[/]")
            console.print("[dim]Use 'carmy month create' to create one.[/]")
            return

        table = Table(title="Month Plans")
        table.add_column("Year", style="cyan")
        table.add_column("Month", style="cyan")
        table.add_column("Season", style="green")
        table.add_column("Theme")
        table.add_column("Status")
        table.add_column("Weeks", justify="right")
        table.add_column("Special Dates", justify="right")

        for plan in plans:
            month_name = MONTH_NAMES[plan.month - 1][:3]
            theme = plan.theme or "-"
            status_color = {
                "draft": "yellow",
                "active": "green",
                "completed": "dim",
            }.get(plan.status, "white")

            table.add_row(
                str(plan.year),
                month_name,
                plan.season,
                theme,
                f"[{status_color}]{plan.status}[/]",
                str(len(plan.week_skeletons)),
                str(len(plan.special_dates)),
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(plans)} plan(s)[/]")


@app.command("create")
def create_month(
    month: int = typer.Option(None, "--month", "-m", help="Month number (1-12)"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
    theme: str = typer.Option(None, "--theme", "-t", help="Theme: comfort, light, seafood, budget, guests, lent"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite if exists"),
) -> None:
    """Create a new month plan.

    If month/year not specified, creates for the current month.
    """
    current_year, current_month = get_current_month()

    if year is None:
        year = current_year
    if month is None:
        month = current_month

    if month < 1 or month > 12:
        console.print(f"[red]Invalid month:[/] {month}. Must be 1-12.")
        raise typer.Exit(1)

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        # Check if exists
        existing = session.execute(
            select(MonthPlan).where(
                MonthPlan.year == year, MonthPlan.month == month
            )
        ).scalar_one_or_none()

        if existing and not force:
            console.print(f"[yellow]Month plan for {MONTH_NAMES[month - 1]} {year} already exists.[/]")
            console.print("Use --force to overwrite.")
            raise typer.Exit(1)

        if existing and force:
            session.delete(existing)
            session.commit()

        # Create new plan
        season = get_season_for_month(month)
        plan = MonthPlan(
            year=year,
            month=month,
            theme=theme,
            season=season,
            status="draft",
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)

        console.print(Panel(
            f"[bold green]Created month plan![/]\n\n"
            f"Month: [cyan]{MONTH_NAMES[month - 1]} {year}[/]\n"
            f"Season: [green]{season}[/]\n"
            f"Theme: {theme or '[dim]none[/]'}\n"
            f"Status: [yellow]draft[/]",
            title="New Month Plan",
        ))

        console.print("\n[dim]Next steps:[/]")
        console.print("  1. Add special dates: [bold]carmy month add-date[/]")
        console.print("  2. Generate weeks: [bold]carmy week generate[/]")


@app.command("show")
def show_month(
    month: int = typer.Option(None, "--month", "-m", help="Month number (1-12)"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
) -> None:
    """Show details of a month plan."""
    current_year, current_month = get_current_month()

    if year is None:
        year = current_year
    if month is None:
        month = current_month

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = session.execute(
            select(MonthPlan).where(
                MonthPlan.year == year, MonthPlan.month == month
            )
        ).scalar_one_or_none()

        if not plan:
            console.print(f"[red]No plan found for {MONTH_NAMES[month - 1]} {year}[/]")
            raise typer.Exit(1)

        # Header
        status_color = {
            "draft": "yellow",
            "active": "green",
            "completed": "dim",
        }.get(plan.status, "white")

        console.print(Panel(
            f"[bold]{MONTH_NAMES[month - 1]} {year}[/]\n"
            f"Season: [green]{plan.season}[/] | "
            f"Theme: {plan.theme or '[dim]none[/]'} | "
            f"Status: [{status_color}]{plan.status}[/]",
            title="Month Plan",
        ))

        # Settings
        if plan.settings:
            console.print("\n[bold]Settings:[/]")
            for key, value in plan.settings.items():
                console.print(f"  {key}: {value}")

        # Special dates
        if plan.special_dates:
            console.print("\n[bold]Special Dates:[/]")
            dates_table = Table(show_header=True, box=None)
            dates_table.add_column("Date", style="cyan")
            dates_table.add_column("Type")
            dates_table.add_column("Name")
            dates_table.add_column("Affects Cooking", justify="center")

            for sd in sorted(plan.special_dates, key=lambda x: x.date):
                affects = "[green]Yes[/]" if sd.affects_cooking else "[dim]No[/]"
                dates_table.add_row(
                    str(sd.date),
                    sd.event_type,
                    sd.name or "-",
                    affects,
                )
            console.print(dates_table)
        else:
            console.print("\n[dim]No special dates[/]")

        # Week skeletons
        if plan.week_skeletons:
            console.print("\n[bold]Week Skeletons:[/]")
            week_table = Table(show_header=True, box=None)
            week_table.add_column("Week", style="cyan")
            week_table.add_column("Start Date")
            week_table.add_column("End Date")
            week_table.add_column("Status")
            week_table.add_column("Events", justify="right")
            week_table.add_column("Slots", justify="right")

            for ws in sorted(plan.week_skeletons, key=lambda x: x.week_number):
                week_table.add_row(
                    f"W{ws.week_number}",
                    str(ws.start_date),
                    str(ws.end_date),
                    ws.status,
                    str(len(ws.cooking_events)),
                    str(len(ws.meal_slots)),
                )
            console.print(week_table)
        else:
            console.print("\n[dim]No week skeletons yet[/]")


@app.command("add-date")
def add_special_date(
    date_str: str = typer.Argument(..., help="Date in YYYY-MM-DD format"),
    event_type: str = typer.Argument(..., help="Type: birthday, name_day, guests, holiday, party, away"),
    name: str = typer.Option(None, "--name", "-n", help="Name/description"),
    no_cooking: bool = typer.Option(False, "--no-cooking", help="This date does not affect cooking"),
    month: int = typer.Option(None, "--month", "-m", help="Month number (auto-detected from date)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (auto-detected from date)"),
) -> None:
    """Add a special date to a month plan.

    Examples:
        carmy month add-date 2025-01-15 birthday --name "John's birthday"
        carmy month add-date 2025-01-20 guests --name "In-laws visiting"
        carmy month add-date 2025-01-25 away --no-cooking
    """
    try:
        special_date = date.fromisoformat(date_str)
    except ValueError:
        console.print(f"[red]Invalid date format:[/] {date_str}. Use YYYY-MM-DD.")
        raise typer.Exit(1)

    # Auto-detect month/year from date
    if year is None:
        year = special_date.year
    if month is None:
        month = special_date.month

    valid_types = ["birthday", "name_day", "guests", "holiday", "party", "away"]
    if event_type not in valid_types:
        console.print(f"[red]Invalid event type:[/] {event_type}")
        console.print(f"Valid types: {', '.join(valid_types)}")
        raise typer.Exit(1)

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = session.execute(
            select(MonthPlan).where(
                MonthPlan.year == year, MonthPlan.month == month
            )
        ).scalar_one_or_none()

        if not plan:
            console.print(f"[red]No plan found for {MONTH_NAMES[month - 1]} {year}[/]")
            console.print("[dim]Create one first with 'carmy month create'[/]")
            raise typer.Exit(1)

        sd = SpecialDate(
            month_plan_id=plan.id,
            date=special_date,
            event_type=event_type,
            name=name,
            affects_cooking=not no_cooking,
        )
        session.add(sd)
        session.commit()

        icon = {
            "birthday": "ðŸŽ‚",
            "name_day": "ðŸŽ‰",
            "guests": "ðŸ‘¥",
            "holiday": "ðŸŽ„",
            "party": "ðŸ¥³",
            "away": "âœˆï¸",
        }.get(event_type, "ðŸ“…")

        console.print(f"[green]Added special date:[/] {icon} {date_str} - {event_type}")
        if name:
            console.print(f"  Name: {name}")
        if no_cooking:
            console.print("  [dim]Does not affect cooking[/]")


@app.command("remove-date")
def remove_special_date(
    date_str: str = typer.Argument(..., help="Date to remove in YYYY-MM-DD format"),
    month: int = typer.Option(None, "--month", "-m", help="Month number"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
) -> None:
    """Remove a special date from a month plan."""
    try:
        special_date = date.fromisoformat(date_str)
    except ValueError:
        console.print(f"[red]Invalid date format:[/] {date_str}. Use YYYY-MM-DD.")
        raise typer.Exit(1)

    if year is None:
        year = special_date.year
    if month is None:
        month = special_date.month

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = session.execute(
            select(MonthPlan).where(
                MonthPlan.year == year, MonthPlan.month == month
            )
        ).scalar_one_or_none()

        if not plan:
            console.print(f"[red]No plan found for {MONTH_NAMES[month - 1]} {year}[/]")
            raise typer.Exit(1)

        sd = session.execute(
            select(SpecialDate).where(
                SpecialDate.month_plan_id == plan.id,
                SpecialDate.date == special_date,
            )
        ).scalar_one_or_none()

        if not sd:
            console.print(f"[yellow]No special date found for {date_str}[/]")
            raise typer.Exit(1)

        session.delete(sd)
        session.commit()

        console.print(f"[green]Removed special date:[/] {date_str}")


@app.command("set-theme")
def set_theme(
    theme: str = typer.Argument(..., help="Theme: comfort, light, seafood, budget, guests, pantry_clearing, lent, none"),
    month: int = typer.Option(None, "--month", "-m", help="Month number"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
) -> None:
    """Set or change the theme for a month plan."""
    current_year, current_month = get_current_month()

    if year is None:
        year = current_year
    if month is None:
        month = current_month

    valid_themes = ["comfort", "light", "seafood", "budget", "guests", "pantry_clearing", "lent", "none"]
    if theme not in valid_themes:
        console.print(f"[red]Invalid theme:[/] {theme}")
        console.print(f"Valid themes: {', '.join(valid_themes)}")
        raise typer.Exit(1)

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = session.execute(
            select(MonthPlan).where(
                MonthPlan.year == year, MonthPlan.month == month
            )
        ).scalar_one_or_none()

        if not plan:
            console.print(f"[red]No plan found for {MONTH_NAMES[month - 1]} {year}[/]")
            raise typer.Exit(1)

        plan.theme = None if theme == "none" else theme
        session.commit()

        console.print(f"[green]Theme updated:[/] {theme} for {MONTH_NAMES[month - 1]} {year}")


@app.command("activate")
def activate_month(
    month: int = typer.Option(None, "--month", "-m", help="Month number"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
) -> None:
    """Activate a month plan (change status from draft to active)."""
    current_year, current_month = get_current_month()

    if year is None:
        year = current_year
    if month is None:
        month = current_month

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = session.execute(
            select(MonthPlan).where(
                MonthPlan.year == year, MonthPlan.month == month
            )
        ).scalar_one_or_none()

        if not plan:
            console.print(f"[red]No plan found for {MONTH_NAMES[month - 1]} {year}[/]")
            raise typer.Exit(1)

        if plan.status == "active":
            console.print(f"[yellow]Plan is already active[/]")
            return

        plan.status = "active"
        session.commit()

        console.print(f"[green]Activated:[/] {MONTH_NAMES[month - 1]} {year}")


@app.command("generate")
def generate_month(
    month: int = typer.Option(None, "--month", "-m", help="Month number"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
    regenerate: bool = typer.Option(False, "--regenerate", "-r", help="Regenerate existing week skeletons"),
) -> None:
    """Generate week skeletons and cooking events for a month.

    Uses the MonthOrchestrator to create cooking events based on:
    - Learned cooking rhythm
    - Month theme and settings
    - Seasonal meal preferences
    - Conflict avoidance (flavor bases, variety)
    """
    from carmy.services.month_orchestrator import MonthOrchestrator, MonthSettings

    current_year, current_month = get_current_month()

    if year is None:
        year = current_year
    if month is None:
        month = current_month

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = session.execute(
            select(MonthPlan).where(
                MonthPlan.year == year, MonthPlan.month == month
            )
        ).scalar_one_or_none()

        if not plan:
            console.print(f"[red]No plan found for {MONTH_NAMES[month - 1]} {year}[/]")
            console.print("[dim]Create one first with 'carmy month create'[/]")
            raise typer.Exit(1)

        # Check if weeks already exist
        if plan.week_skeletons and not regenerate:
            console.print(f"[yellow]Week skeletons already exist for {MONTH_NAMES[month - 1]} {year}[/]")
            console.print("Use --regenerate to overwrite.")
            raise typer.Exit(1)

        # Delete existing week skeletons if regenerating
        if plan.week_skeletons and regenerate:
            for ws in plan.week_skeletons:
                session.delete(ws)
            session.commit()
            session.refresh(plan)

        # Create settings from plan
        settings = MonthSettings.from_dict(plan.settings or {})

        # Generate the month
        console.print(f"[bold]Generating week skeletons for {MONTH_NAMES[month - 1]} {year}...[/]")
        orchestrator = MonthOrchestrator(session)
        generated = orchestrator.generate_month(year, month, settings, plan.theme)

        # Save to database
        orchestrator.save_month(generated, plan)

        # Display results
        console.print(f"\n[green]Generated {len(generated.weeks)} week skeletons![/]")
        console.print(f"Season: [cyan]{generated.season}[/]")
        if generated.theme:
            console.print(f"Theme: [cyan]{generated.theme}[/]")

        table = Table(title="Generated Weeks")
        table.add_column("Week", style="cyan")
        table.add_column("Start Date")
        table.add_column("End Date")
        table.add_column("Soups", justify="right")
        table.add_column("Mains", justify="right")

        for week in generated.weeks:
            table.add_row(
                f"W{week.week_number}",
                str(week.start_date),
                str(week.end_date),
                str(len(week.soup_slots)),
                str(len(week.cooking_slots)),
            )

        console.print(table)

        if generated.warnings:
            console.print("\n[yellow]Warnings:[/]")
            for warning in generated.warnings:
                console.print(f"  - {warning}")

        console.print("\n[dim]Next steps:[/]")
        console.print("  1. View weeks: [bold]carmy week list[/]")
        console.print("  2. Materialize a week: [bold]carmy week materialize[/]")


@app.command("themes")
def list_themes() -> None:
    """List available themes for month planning."""
    from carmy.services.theme_settings import THEMES

    console.print("\n[bold]Available Themes[/]\n")

    for name, theme in THEMES.items():
        console.print(f"  [bold cyan]{name}[/]")
        console.print(f"     {theme.description}")

        effects = []
        if theme.meat_delta != 0:
            sign = "+" if theme.meat_delta > 0 else ""
            effects.append(f"meat {sign}{theme.meat_delta:.1f}")
        if theme.fish_delta != 0:
            sign = "+" if theme.fish_delta > 0 else ""
            effects.append(f"fish {sign}{theme.fish_delta:.1f}")
        if theme.veggie_delta != 0:
            sign = "+" if theme.veggie_delta > 0 else ""
            effects.append(f"veggie {sign}{theme.veggie_delta:.1f}")
        if theme.lent_mode:
            effects.append("lent mode")
        if theme.batch_cooking:
            effects.append("batch cooking")

        if effects:
            console.print(f"     [dim]Effects: {', '.join(effects)}[/]")
        console.print()


@app.command("settings")
def show_settings(
    month: int = typer.Option(None, "--month", "-m", help="Month number"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
) -> None:
    """Show current settings for a month plan."""
    from carmy.services.theme_settings import MonthSettingsV2

    current_year, current_month = get_current_month()
    if year is None:
        year = current_year
    if month is None:
        month = current_month

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = session.execute(
            select(MonthPlan).where(
                MonthPlan.year == year, MonthPlan.month == month
            )
        ).scalar_one_or_none()

        if not plan:
            console.print(f"[red]No plan found for {MONTH_NAMES[month - 1]} {year}[/]")
            raise typer.Exit(1)

        settings = MonthSettingsV2.from_dict(plan.settings or {})

        console.print(Panel(
            f"[bold]{MONTH_NAMES[month - 1]} {year}[/]\nTheme: [cyan]{plan.theme or 'none'}[/]",
            title="Month Settings",
        ))

        console.print("\n[bold]Dietary Sliders:[/]")
        _print_slider("Meat level", settings.meat_level)
        _print_slider("Fish level", settings.fish_level)
        _print_slider("Veggie level", settings.veggie_level)
        _print_slider("New recipes", settings.new_recipes)
        _print_slider("Cuisine balance", settings.cuisine_balance, "Hungarian", "International")

        console.print("\n[bold]Special Modes:[/]")
        console.print(f"  Lent mode: {'[green]ON[/]' if settings.lent_mode else '[dim]off[/]'}")
        console.print(f"  Batch cooking: {'[green]ON[/]' if settings.batch_cooking else '[dim]off[/]'}")

        console.print("\n[bold]Weekly Quotas:[/]")
        console.print(f"  Soups per week: {settings.soups_per_week}")
        console.print(f"  Main courses per week: {settings.main_courses_per_week}")
        console.print(f"  Max meat per week: {settings.max_meat_per_week}")

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        console.print("\n[bold]Cooking Days:[/]")
        big_cook = [day_names[d] for d in settings.big_cook_days]
        mid_week = [day_names[d] for d in settings.mid_week_cook_days]
        fun_food = [day_names[d] for d in settings.fun_food_days]
        console.print(f"  Big cook days: {', '.join(big_cook) or 'none'}")
        console.print(f"  Mid-week cook days: {', '.join(mid_week) or 'none'}")
        console.print(f"  Fun food days: {', '.join(fun_food) or 'none'}")


def _print_slider(name: str, value: float, low_label: str = "Low", high_label: str = "High") -> None:
    """Print a visual slider."""
    bar_width = 20
    filled = int(value * bar_width)
    empty = bar_width - filled
    bar = "[green]" + "=" * filled + "[/][dim]" + "-" * empty + "[/]"
    console.print(f"  {name}: {bar} {value:.1f} ({low_label} <-> {high_label})")


@app.command("set")
def set_setting(
    setting: str = typer.Argument(..., help="Setting name"),
    value: str = typer.Argument(..., help="Setting value"),
    month: int = typer.Option(None, "--month", "-m", help="Month number"),
    year: int = typer.Option(None, "--year", "-y", help="Year"),
) -> None:
    """Set a specific setting for a month plan."""
    from carmy.services.theme_settings import MonthSettingsV2

    current_year, current_month = get_current_month()
    if year is None:
        year = current_year
    if month is None:
        month = current_month

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = session.execute(
            select(MonthPlan).where(MonthPlan.year == year, MonthPlan.month == month)
        ).scalar_one_or_none()

        if not plan:
            console.print(f"[red]No plan found for {MONTH_NAMES[month - 1]} {year}[/]")
            raise typer.Exit(1)

        # Copy settings to ensure SQLAlchemy detects the change
        current_settings = dict(plan.settings) if plan.settings else {}
        float_settings = ["meat_level", "fish_level", "veggie_level", "new_recipes", "cuisine_balance"]
        bool_settings = ["lent_mode", "batch_cooking", "sales_aware"]
        int_settings = ["soups_per_week", "main_courses_per_week", "max_meat_per_week"]
        list_settings = ["big_cook_days", "mid_week_cook_days", "fun_food_days"]

        try:
            if setting in float_settings:
                parsed_value = float(value)
                if not 0.0 <= parsed_value <= 1.0:
                    console.print("[red]Value must be between 0.0 and 1.0[/]")
                    raise typer.Exit(1)
                current_settings[setting] = parsed_value
            elif setting in bool_settings:
                current_settings[setting] = value.lower() in ("true", "1", "yes", "on")
            elif setting in int_settings:
                current_settings[setting] = int(value)
            elif setting in list_settings:
                current_settings[setting] = [int(v.strip()) for v in value.split(",")]
            else:
                console.print(f"[red]Unknown setting:[/] {setting}")
                raise typer.Exit(1)
        except ValueError as e:
            console.print(f"[red]Invalid value:[/] {e}")
            raise typer.Exit(1)

        test_settings = MonthSettingsV2.from_dict(current_settings)
        errors = test_settings.validate()
        if errors:
            for error in errors:
                console.print(f"[red]Validation error:[/] {error}")
            raise typer.Exit(1)

        plan.settings = current_settings
        session.commit()
        console.print(f"[green]Updated:[/] {setting} = {value}")
