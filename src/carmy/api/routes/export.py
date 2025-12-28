"""Export API routes."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from carmy.api.deps import get_db
from carmy.models.plan import WeeklyPlan
from carmy.services.export import ExportService

router = APIRouter()


def get_plan_or_404(db: Session, year: int, week: int) -> WeeklyPlan:
    """Get a plan by year/week or raise 404."""
    plan = db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.year == year, WeeklyPlan.week_number == week
        )
    ).scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan for week {week}, {year}")

    return plan


@router.get("/{year}/{week}/json")
def export_json(year: int, week: int, db: Session = Depends(get_db)) -> dict:
    """Export plan as JSON."""
    plan = get_plan_or_404(db, year, week)
    service = ExportService(db)
    import json
    return json.loads(service.export_plan_json(plan))


@router.get("/{year}/{week}/csv", response_class=PlainTextResponse)
def export_csv(year: int, week: int, db: Session = Depends(get_db)) -> str:
    """Export plan as CSV."""
    plan = get_plan_or_404(db, year, week)
    service = ExportService(db)
    return service.export_plan_csv(plan)


@router.get("/{year}/{week}/markdown", response_class=PlainTextResponse)
def export_markdown(year: int, week: int, db: Session = Depends(get_db)) -> str:
    """Export plan as Markdown."""
    plan = get_plan_or_404(db, year, week)
    service = ExportService(db)
    return service.export_plan_markdown(plan)


@router.get("/{year}/{week}/ics", response_class=PlainTextResponse)
def export_ics(year: int, week: int, db: Session = Depends(get_db)) -> str:
    """Export plan as ICS calendar file."""
    plan = get_plan_or_404(db, year, week)
    service = ExportService(db)
    return service.export_plan_ics(plan)


@router.get("/{year}/{week}/shopping", response_class=PlainTextResponse)
def export_shopping(year: int, week: int, db: Session = Depends(get_db)) -> str:
    """Export shopping list."""
    plan = get_plan_or_404(db, year, week)
    service = ExportService(db)
    shopping_list = service.generate_shopping_list(plan)
    return shopping_list.to_text()
