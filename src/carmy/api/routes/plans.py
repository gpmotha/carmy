"""Plan API routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from carmy.api.deps import get_db
from carmy.api.schemas.plan import PlanResponse, PlanSummary
from carmy.models.plan import WeeklyPlan
from carmy.services.generator import GeneratorConfig, PlanGenerator
from carmy.services.rules_engine import RulesEngine

router = APIRouter()


def get_current_week() -> tuple[int, int]:
    """Get current ISO year and week number."""
    today = date.today()
    iso = today.isocalendar()
    return iso[0], iso[1]


def get_week_start(year: int, week: int) -> date:
    """Get the Monday of a given ISO week."""
    jan_4 = date(year, 1, 4)
    start_of_week_1 = jan_4 - timedelta(days=jan_4.weekday())
    return start_of_week_1 + timedelta(weeks=week - 1)


@router.get("", response_model=list[PlanSummary])
def list_plans(
    year: int | None = Query(None, description="Filter by year"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List all weekly plans."""
    query = select(WeeklyPlan).order_by(
        WeeklyPlan.year.desc(), WeeklyPlan.week_number.desc()
    )

    if year:
        query = query.where(WeeklyPlan.year == year)

    query = query.limit(limit)
    plans = db.execute(query).scalars().all()

    result = []
    for plan in plans:
        meals = [pm for pm in plan.plan_meals if pm.meal]
        soups = [pm for pm in meals if pm.meal.meal_type == "soup"]
        mains = [pm for pm in meals if pm.meal.meal_type in ("main_course", "pasta", "dinner")]

        result.append({
            "id": plan.id,
            "year": plan.year,
            "week_number": plan.week_number,
            "start_date": plan.start_date,
            "meal_count": len(meals),
            "soup_count": len(soups),
            "main_count": len(mains),
        })

    return result


@router.get("/current", response_model=PlanResponse)
def get_current_plan(db: Session = Depends(get_db)) -> WeeklyPlan:
    """Get the current week's plan."""
    year, week = get_current_week()
    plan = db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.year == year, WeeklyPlan.week_number == week
        )
    ).scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan for week {week}, {year}")

    return plan


@router.get("/{year}/{week}", response_model=PlanResponse)
def get_plan(year: int, week: int, db: Session = Depends(get_db)) -> WeeklyPlan:
    """Get a specific weekly plan."""
    plan = db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.year == year, WeeklyPlan.week_number == week
        )
    ).scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan for week {week}, {year}")

    return plan


@router.get("/{year}/{week}/validate")
def validate_plan(year: int, week: int, db: Session = Depends(get_db)) -> dict:
    """Validate a weekly plan against rules."""
    plan = db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.year == year, WeeklyPlan.week_number == week
        )
    ).scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan for week {week}, {year}")

    rules = RulesEngine()
    result = rules.validate(plan)

    return {
        "is_valid": result.is_valid,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
        "violations": [
            {
                "rule": v.rule_type.value,
                "message": v.message,
                "severity": v.severity.value,
            }
            for v in result.violations
        ],
        "stats": result.stats,
    }


@router.post("/generate")
def generate_plan(
    week: int | None = Query(None, description="Week number (defaults to next week)"),
    year: int | None = Query(None, description="Year (defaults to current)"),
    randomness: float = Query(0.3, ge=0.0, le=1.0),
    save: bool = Query(False, description="Save the generated plan"),
    force: bool = Query(False, description="Overwrite existing plan if present"),
    db: Session = Depends(get_db),
) -> dict:
    """Generate a new weekly plan."""
    current_year, current_week = get_current_week()

    if year is None:
        year = current_year
    if week is None:
        week = current_week + 1
        if week > 52:
            week = 1
            year += 1

    # Check if plan already exists
    existing = db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.year == year, WeeklyPlan.week_number == week
        )
    ).scalar_one_or_none()

    if existing and not force:
        raise HTTPException(
            status_code=409,
            detail=f"Plan for week {week}, {year} already exists. Use force=true to overwrite."
        )

    # Delete existing plan if force is true
    if existing and force:
        from carmy.models.plan import PlanMeal
        # Delete all plan meals first
        db.execute(select(PlanMeal).where(PlanMeal.plan_id == existing.id))
        db.query(PlanMeal).filter(PlanMeal.plan_id == existing.id).delete()
        db.delete(existing)
        db.flush()

    start_date = get_week_start(year, week)
    config = GeneratorConfig(randomness=randomness)
    generator = PlanGenerator(db, config)

    plan = generator.generate(year, week, start_date)

    result = {
        "year": plan.year,
        "week_number": plan.week_number,
        "start_date": plan.start_date.isoformat(),
        "season": plan.season,
        "soups": [{"id": s.id, "name": s.name, "cuisine": s.cuisine} for s in plan.soups],
        "main_courses": [
            {"id": m.id, "name": m.name, "cuisine": m.cuisine, "has_meat": m.has_meat}
            for m in plan.main_courses
        ],
        "validation": None,
        "saved": False,
    }

    if plan.validation:
        result["validation"] = {
            "is_valid": plan.validation.is_valid,
            "violations": [
                {"rule": v.rule_type.value, "message": v.message, "severity": v.severity.value}
                for v in plan.validation.violations
            ],
        }

    if save:
        saved_plan = generator.save_plan(plan)
        result["saved"] = True
        result["id"] = saved_plan.id

    return result
