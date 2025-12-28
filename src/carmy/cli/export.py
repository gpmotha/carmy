"""Export commands for Carmy CLI."""

from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from carmy.models.database import get_engine, init_db
from carmy.models.plan import WeeklyPlan
from carmy.models.week_skeleton import WeekSkeleton
from carmy.models.cooking_event import CookingEvent
from carmy.models.meal_slot import MealSlot
from carmy.services.export import ExportService, V2ExportService

app = typer.Typer(help="Export plans and shopping lists")
console = Console()


def get_current_week() -> tuple[int, int]:
    """Get current ISO year and week number."""
    today = date.today()
    iso = today.isocalendar()
    return iso[0], iso[1]


def get_plan(session: Session, week: int, year: int) -> WeeklyPlan | None:
    """Get a plan by week and year."""
    return session.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.year == year, WeeklyPlan.week_number == week
        )
    ).scalar_one_or_none()


@app.command("shopping")
def export_shopping_list(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text, markdown"),
) -> None:
    """Generate a shopping list from a weekly plan."""
    current_year, current_week = get_current_week()
    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = get_plan(session, week, year)

        if not plan:
            console.print(f"[red]No plan found for week {week}, {year}[/]")
            raise typer.Exit(1)

        service = ExportService(session)
        shopping_list = service.generate_shopping_list(plan)

        if format == "markdown":
            content = shopping_list.to_markdown()
        else:
            content = shopping_list.to_text()

        if output:
            output.write_text(content, encoding="utf-8")
            console.print(f"[green]Shopping list saved to:[/] {output}")
        else:
            console.print(Panel(content, title="Shopping List"))


@app.command("json")
def export_json(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export a plan as JSON."""
    current_year, current_week = get_current_week()
    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = get_plan(session, week, year)

        if not plan:
            console.print(f"[red]No plan found for week {week}, {year}[/]")
            raise typer.Exit(1)

        service = ExportService(session)
        content = service.export_plan_json(plan)

        if output:
            output.write_text(content, encoding="utf-8")
            console.print(f"[green]JSON exported to:[/] {output}")
        else:
            console.print(content)


@app.command("markdown")
def export_markdown(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
    lang: str = typer.Option("en", "--lang", "-l", help="Language for meal names: en, hu"),
) -> None:
    """Export a plan as Markdown."""
    current_year, current_week = get_current_week()
    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = get_plan(session, week, year)

        if not plan:
            console.print(f"[red]No plan found for week {week}, {year}[/]")
            raise typer.Exit(1)

        service = ExportService(session)
        content = service.export_plan_markdown(plan, lang=lang)

        if output:
            output.write_text(content, encoding="utf-8")
            console.print(f"[green]Markdown exported to:[/] {output}")
        else:
            console.print(content)


@app.command("csv")
def export_csv(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export a plan as CSV."""
    current_year, current_week = get_current_week()
    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = get_plan(session, week, year)

        if not plan:
            console.print(f"[red]No plan found for week {week}, {year}[/]")
            raise typer.Exit(1)

        service = ExportService(session)
        content = service.export_plan_csv(plan)

        if output:
            output.write_text(content, encoding="utf-8")
            console.print(f"[green]CSV exported to:[/] {output}")
        else:
            console.print(content)


@app.command("calendar")
def export_calendar(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path (default: week_N.ics)"),
) -> None:
    """Export a plan as ICS calendar file."""
    current_year, current_week = get_current_week()
    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = get_plan(session, week, year)

        if not plan:
            console.print(f"[red]No plan found for week {week}, {year}[/]")
            raise typer.Exit(1)

        service = ExportService(session)
        content = service.export_plan_ics(plan)

        if output is None:
            output = Path(f"week_{week}_{year}.ics")

        output.write_text(content, encoding="utf-8")
        console.print(f"[green]Calendar exported to:[/] {output}")
        console.print("[dim]Import this file into Google Calendar, Outlook, or Apple Calendar[/]")


@app.command("all")
def export_all(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    output_dir: Path = typer.Option(Path("."), "--dir", "-d", help="Output directory"),
) -> None:
    """Export a plan in all formats at once."""
    current_year, current_week = get_current_week()
    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        plan = get_plan(session, week, year)

        if not plan:
            console.print(f"[red]No plan found for week {week}, {year}[/]")
            raise typer.Exit(1)

        service = ExportService(session)
        prefix = f"week_{week}_{year}"

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export all formats
        files = []

        # JSON
        json_path = output_dir / f"{prefix}.json"
        json_path.write_text(service.export_plan_json(plan), encoding="utf-8")
        files.append(json_path)

        # Markdown
        md_path = output_dir / f"{prefix}.md"
        md_path.write_text(service.export_plan_markdown(plan), encoding="utf-8")
        files.append(md_path)

        # CSV
        csv_path = output_dir / f"{prefix}.csv"
        csv_path.write_text(service.export_plan_csv(plan), encoding="utf-8")
        files.append(csv_path)

        # ICS
        ics_path = output_dir / f"{prefix}.ics"
        ics_path.write_text(service.export_plan_ics(plan), encoding="utf-8")
        files.append(ics_path)

        # Shopping list
        shopping = service.generate_shopping_list(plan)
        shopping_path = output_dir / f"{prefix}_shopping.txt"
        shopping_path.write_text(shopping.to_text(), encoding="utf-8")
        files.append(shopping_path)

        console.print(f"[green]Exported week {week}, {year} to {output_dir}:[/]")
        for f in files:
            console.print(f"  - {f.name}")


# ============== V2 EXPORT COMMANDS ==============


def get_skeleton(session: Session, week: int, year: int) -> WeekSkeleton | None:
    """Get a v2 week skeleton with relationships."""
    return session.execute(
        select(WeekSkeleton)
        .where(WeekSkeleton.year == year, WeekSkeleton.week_number == week)
        .options(
            selectinload(WeekSkeleton.cooking_events).selectinload(CookingEvent.meal),
            selectinload(WeekSkeleton.meal_slots).selectinload(MealSlot.meal),
        )
    ).scalar_one_or_none()


@app.command("week-ics")
def export_week_ics(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export a v2 week skeleton as ICS calendar file."""
    current_year, current_week = get_current_week()
    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        skeleton = get_skeleton(session, week, year)

        if not skeleton:
            console.print(f"[red]No week skeleton found for {year}-W{week}[/]")
            raise typer.Exit(1)

        if not skeleton.meal_slots:
            console.print(f"[yellow]Week {year}-W{week} has no meal slots.[/]")
            console.print("[dim]Run 'carmy week materialize' first.[/]")
            raise typer.Exit(1)

        service = V2ExportService(session)
        content = service.generate_week_ics(skeleton)

        if output is None:
            output = Path(f"carmy-week-{year}-{week}.ics")

        output.write_text(content, encoding="utf-8")
        console.print(f"[green]Calendar exported to:[/] {output}")
        console.print(f"  {len(skeleton.meal_slots)} meal slots exported")
        console.print("[dim]Import this file into Google Calendar, Outlook, or Apple Calendar[/]")


@app.command("week-html")
def export_week_html(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export a v2 week skeleton as HTML for printing/sharing."""
    current_year, current_week = get_current_week()
    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        skeleton = get_skeleton(session, week, year)

        if not skeleton:
            console.print(f"[red]No week skeleton found for {year}-W{week}[/]")
            raise typer.Exit(1)

        if not skeleton.meal_slots:
            console.print(f"[yellow]Week {year}-W{week} has no meal slots.[/]")
            raise typer.Exit(1)

        service = V2ExportService(session)
        content = service.generate_week_html(skeleton)

        if output is None:
            output = Path(f"carmy-week-{year}-{week}.html")

        output.write_text(content, encoding="utf-8")
        console.print(f"[green]HTML exported to:[/] {output}")
        console.print("[dim]Open in browser or print to PDF[/]")


@app.command("week-shopping")
def export_week_shopping(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("text", "--format", "-f", help="Format: text, markdown"),
) -> None:
    """Generate a shopping list from a v2 week skeleton."""
    current_year, current_week = get_current_week()
    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        skeleton = get_skeleton(session, week, year)

        if not skeleton:
            console.print(f"[red]No week skeleton found for {year}-W{week}[/]")
            raise typer.Exit(1)

        if not skeleton.meal_slots:
            console.print(f"[yellow]Week {year}-W{week} has no meal slots.[/]")
            raise typer.Exit(1)

        service = V2ExportService(session)
        shopping_list = service.generate_shopping_list(skeleton)

        if format == "markdown":
            content = shopping_list.to_markdown()
        else:
            content = shopping_list.to_text()

        if output:
            output.write_text(content, encoding="utf-8")
            console.print(f"[green]Shopping list saved to:[/] {output}")
        else:
            console.print(Panel(content, title="Shopping List"))

        console.print(f"\n[cyan]Fresh meals to cook:[/] {len(shopping_list.fresh_meals)}")
        console.print(f"[yellow]Leftover meals:[/] {len(shopping_list.leftover_meals)}")


@app.command("week-all")
def export_week_all(
    week: int = typer.Option(None, "--week", "-w", help="Week number (defaults to current)"),
    year: int = typer.Option(None, "--year", "-y", help="Year (defaults to current)"),
    output_dir: Path = typer.Option(Path("."), "--dir", "-d", help="Output directory"),
) -> None:
    """Export a v2 week skeleton in all formats."""
    current_year, current_week = get_current_week()
    if year is None:
        year = current_year
    if week is None:
        week = current_week

    init_db()
    engine = get_engine()

    with Session(engine) as session:
        skeleton = get_skeleton(session, week, year)

        if not skeleton:
            console.print(f"[red]No week skeleton found for {year}-W{week}[/]")
            raise typer.Exit(1)

        if not skeleton.meal_slots:
            console.print(f"[yellow]Week {year}-W{week} has no meal slots.[/]")
            raise typer.Exit(1)

        service = V2ExportService(session)
        prefix = f"carmy-week-{year}-{week}"

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        files = []

        # ICS Calendar
        ics_path = output_dir / f"{prefix}.ics"
        ics_path.write_text(service.generate_week_ics(skeleton), encoding="utf-8")
        files.append(("Calendar (ICS)", ics_path))

        # HTML
        html_path = output_dir / f"{prefix}.html"
        html_path.write_text(service.generate_week_html(skeleton), encoding="utf-8")
        files.append(("HTML", html_path))

        # Markdown
        md_path = output_dir / f"{prefix}.md"
        md_path.write_text(service.generate_week_markdown(skeleton), encoding="utf-8")
        files.append(("Markdown", md_path))

        # JSON
        json_path = output_dir / f"{prefix}.json"
        json_path.write_text(service.generate_week_json(skeleton), encoding="utf-8")
        files.append(("JSON", json_path))

        # Shopping list
        shopping = service.generate_shopping_list(skeleton)
        shopping_txt_path = output_dir / f"{prefix}-shopping.txt"
        shopping_txt_path.write_text(shopping.to_text(), encoding="utf-8")
        files.append(("Shopping List", shopping_txt_path))

        console.print(f"[green]Exported week {year}-W{week} to {output_dir}:[/]")
        for label, f in files:
            console.print(f"  - {label}: {f.name}")

        console.print(f"\n[dim]{len(skeleton.meal_slots)} meal slots exported[/]")
