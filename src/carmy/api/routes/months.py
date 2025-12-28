"""MonthPlan API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from carmy.api.deps import get_db
from carmy.api.schemas.month import (
    MonthPlanCreate,
    MonthPlanResponse,
    MonthPlanSummary,
    MonthPlanUpdate,
    SpecialDateCreate,
    SpecialDateResponse,
    SpecialDateUpdate,
)
from carmy.models.month_plan import MonthPlan, SpecialDate, get_season_for_month

router = APIRouter(prefix="/months", tags=["months"])


@router.get("", response_model=list[MonthPlanSummary])
def list_month_plans(
    year: int | None = Query(None, description="Filter by year"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List all month plans."""
    query = select(MonthPlan).order_by(MonthPlan.year.desc(), MonthPlan.month.desc())

    if year:
        query = query.where(MonthPlan.year == year)

    query = query.limit(limit)
    plans = db.execute(query).scalars().all()

    return [
        {
            "id": p.id,
            "year": p.year,
            "month": p.month,
            "theme": p.theme,
            "season": p.season,
            "status": p.status,
            "week_count": len(p.week_skeletons),
            "special_date_count": len(p.special_dates),
        }
        for p in plans
    ]


@router.post("", response_model=MonthPlanResponse)
def create_month_plan(
    data: MonthPlanCreate,
    db: Session = Depends(get_db),
) -> MonthPlan:
    """Create a new month plan."""
    # Check if plan already exists
    existing = db.execute(
        select(MonthPlan).where(
            MonthPlan.year == data.year, MonthPlan.month == data.month
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Month plan for {data.year}-{data.month:02d} already exists"
        )

    # Auto-detect season if not provided
    season = data.season or get_season_for_month(data.month)

    plan = MonthPlan(
        year=data.year,
        month=data.month,
        theme=data.theme,
        season=season,
        settings=data.settings,
    )
    db.add(plan)
    db.flush()

    # Add special dates
    for sd in data.special_dates:
        special_date = SpecialDate(
            month_plan_id=plan.id,
            date=sd.date,
            event_type=sd.event_type,
            name=sd.name,
            affects_cooking=sd.affects_cooking,
            notes=sd.notes,
        )
        db.add(special_date)

    db.commit()
    db.refresh(plan)
    return plan


@router.get("/current", response_model=MonthPlanResponse)
def get_current_month_plan(db: Session = Depends(get_db)) -> MonthPlan:
    """Get the current month's plan."""
    from datetime import date

    today = date.today()
    plan = db.execute(
        select(MonthPlan).where(
            MonthPlan.year == today.year, MonthPlan.month == today.month
        )
    ).scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=404,
            detail=f"No plan for {today.year}-{today.month:02d}"
        )

    return plan


@router.get("/{year}/{month}", response_model=MonthPlanResponse)
def get_month_plan(
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> MonthPlan:
    """Get a specific month plan."""
    plan = db.execute(
        select(MonthPlan).where(MonthPlan.year == year, MonthPlan.month == month)
    ).scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan for {year}-{month:02d}")

    return plan


@router.patch("/{year}/{month}", response_model=MonthPlanResponse)
def update_month_plan(
    year: int,
    month: int,
    data: MonthPlanUpdate,
    db: Session = Depends(get_db),
) -> MonthPlan:
    """Update a month plan."""
    plan = db.execute(
        select(MonthPlan).where(MonthPlan.year == year, MonthPlan.month == month)
    ).scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan for {year}-{month:02d}")

    if data.theme is not None:
        plan.theme = data.theme
    if data.season is not None:
        plan.season = data.season
    if data.settings is not None:
        plan.settings = data.settings
    if data.status is not None:
        plan.status = data.status

    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{year}/{month}")
def delete_month_plan(
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a month plan."""
    plan = db.execute(
        select(MonthPlan).where(MonthPlan.year == year, MonthPlan.month == month)
    ).scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan for {year}-{month:02d}")

    db.delete(plan)
    db.commit()
    return {"success": True, "deleted": f"{year}-{month:02d}"}


# ============== SPECIAL DATES ==============

@router.get("/{year}/{month}/dates", response_model=list[SpecialDateResponse])
def list_special_dates(
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> list[SpecialDate]:
    """List special dates for a month plan."""
    plan = db.execute(
        select(MonthPlan).where(MonthPlan.year == year, MonthPlan.month == month)
    ).scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan for {year}-{month:02d}")

    return plan.special_dates


@router.post("/{year}/{month}/dates", response_model=SpecialDateResponse)
def add_special_date(
    year: int,
    month: int,
    data: SpecialDateCreate,
    db: Session = Depends(get_db),
) -> SpecialDate:
    """Add a special date to a month plan."""
    plan = db.execute(
        select(MonthPlan).where(MonthPlan.year == year, MonthPlan.month == month)
    ).scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan for {year}-{month:02d}")

    special_date = SpecialDate(
        month_plan_id=plan.id,
        date=data.date,
        event_type=data.event_type,
        name=data.name,
        affects_cooking=data.affects_cooking,
        notes=data.notes,
    )
    db.add(special_date)
    db.commit()
    db.refresh(special_date)
    return special_date


@router.patch("/{year}/{month}/dates/{date_id}", response_model=SpecialDateResponse)
def update_special_date(
    year: int,
    month: int,
    date_id: int,
    data: SpecialDateUpdate,
    db: Session = Depends(get_db),
) -> SpecialDate:
    """Update a special date."""
    special_date = db.execute(
        select(SpecialDate).where(SpecialDate.id == date_id)
    ).scalar_one_or_none()

    if not special_date:
        raise HTTPException(status_code=404, detail="Special date not found")

    if data.date is not None:
        special_date.date = data.date
    if data.event_type is not None:
        special_date.event_type = data.event_type
    if data.name is not None:
        special_date.name = data.name
    if data.affects_cooking is not None:
        special_date.affects_cooking = data.affects_cooking
    if data.notes is not None:
        special_date.notes = data.notes

    db.commit()
    db.refresh(special_date)
    return special_date


@router.delete("/{year}/{month}/dates/{date_id}")
def delete_special_date(
    year: int,
    month: int,
    date_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a special date."""
    special_date = db.execute(
        select(SpecialDate).where(SpecialDate.id == date_id)
    ).scalar_one_or_none()

    if not special_date:
        raise HTTPException(status_code=404, detail="Special date not found")

    db.delete(special_date)
    db.commit()
    return {"success": True, "deleted_id": date_id}


# ============== GENERATION ==============

@router.post("/{year}/{month}/generate")
def generate_month_plan(
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> dict:
    """Generate week skeletons and cooking events for a month.

    Uses the MonthOrchestrator to create cooking events based on:
    - Learned cooking rhythm
    - Month theme and settings
    - Seasonal meal preferences
    - Conflict avoidance (flavor bases, variety)
    """
    from carmy.services.month_orchestrator import MonthOrchestrator, MonthSettings

    # Get the month plan
    plan = db.execute(
        select(MonthPlan).where(MonthPlan.year == year, MonthPlan.month == month)
    ).scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan for {year}-{month:02d}")

    # Create settings from plan
    settings = MonthSettings.from_dict(plan.settings or {})

    # Generate the month
    orchestrator = MonthOrchestrator(db)
    generated = orchestrator.generate_month(year, month, settings, plan.theme)

    # Save to database
    orchestrator.save_month(generated, plan)

    # Build response
    weeks_summary = []
    for week in generated.weeks:
        cooking_events = len(week.cooking_slots) + len(week.soup_slots)
        weeks_summary.append({
            "year": week.year,
            "week_number": week.week_number,
            "start_date": str(week.start_date),
            "end_date": str(week.end_date),
            "cooking_events": cooking_events,
            "soups": len(week.soup_slots),
            "mains": len(week.cooking_slots),
        })

    return {
        "success": True,
        "year": year,
        "month": month,
        "season": generated.season,
        "theme": generated.theme,
        "weeks_generated": len(generated.weeks),
        "weeks": weeks_summary,
        "warnings": generated.warnings,
    }
