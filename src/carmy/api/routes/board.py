"""Board API routes for the planning board."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from carmy.api.deps import get_db
from carmy.api.schemas.board import (
    BoardData,
    BoardDay,
    BoardMonth,
    BoardSlot,
    BoardWeek,
    MonthBoardData,
    MonthDay,
    MonthWeekRow,
    PoolMeal,
    PoolSection,
    SlotAssignRequest,
)
from carmy.api.schemas.meal import MealResponse
from carmy.models.meal import Meal
from carmy.models.plan import PlanMeal, WeeklyPlan

router = APIRouter(prefix="/board", tags=["board"])


def get_week_dates(year: int, week: int) -> tuple[date, date]:
    """Get start and end dates for ISO week."""
    jan_4 = date(year, 1, 4)
    start_of_week_1 = jan_4 - timedelta(days=jan_4.weekday())
    start_date = start_of_week_1 + timedelta(weeks=week - 1)
    end_date = start_date + timedelta(days=6)
    return start_date, end_date


def get_current_week() -> tuple[int, int]:
    """Get current ISO year and week number."""
    today = date.today()
    iso = today.isocalendar()
    return iso[0], iso[1]


@router.get("/week/{year}/{week}", response_model=BoardData)
def get_week_board(year: int, week: int, db: Session = Depends(get_db)) -> BoardData:
    """Get board data for a specific week."""
    start_date, end_date = get_week_dates(year, week)

    # Get or find existing plan
    plan = (
        db.query(WeeklyPlan)
        .filter(WeeklyPlan.year == year, WeeklyPlan.week_number == week)
        .first()
    )

    # Build days structure
    days = []
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    slot_types = ["breakfast", "lunch", "dinner", "snack"]

    for i in range(7):
        day_date = start_date + timedelta(days=i)
        slots = {}

        for slot_type in slot_types:
            slot = BoardSlot()

            if plan:
                # Find meal for this slot
                plan_meal = (
                    db.query(PlanMeal)
                    .filter(
                        PlanMeal.plan_id == plan.id,
                        PlanMeal.day_of_week == i,
                        PlanMeal.meal_slot == slot_type,
                    )
                    .first()
                )

                if plan_meal and plan_meal.meal:
                    slot = BoardSlot(
                        plan_meal_id=plan_meal.id,
                        meal=MealResponse.model_validate(plan_meal.meal),
                        is_leftover=plan_meal.is_leftover,
                        portions_remaining=plan_meal.portions_remaining,
                        chain_id=plan_meal.chain_id,
                    )

            slots[slot_type] = slot

        days.append(
            BoardDay(
                day_of_week=i,
                day_name=day_names[i],
                date=day_date,
                slots=slots,
            )
        )

    week_data = BoardWeek(
        year=year,
        week=week,
        start_date=start_date,
        end_date=end_date,
        plan_id=plan.id if plan else None,
        days=days,
    )

    # Build meal pool
    pool = build_meal_pool(db)

    # Get suggestions (seasonal meals)
    suggestions = get_seasonal_suggestions(db)

    # Get recently used meals
    recently_used = get_recently_used(db)

    return BoardData(
        week=week_data,
        pool=pool,
        suggestions=suggestions,
        recently_used=recently_used,
    )


def build_meal_pool(db: Session) -> list[PoolSection]:
    """Build categorized meal pool for sidebar."""
    type_config = [
        ("soup", "Soups", "🍲"),
        ("main_course", "Main Courses", "🍽️"),
        ("breakfast", "Breakfast", "🥣"),
        ("pasta", "Pasta", "🍝"),
        ("salad", "Salads", "🥗"),
        ("dessert", "Desserts", "🍰"),
    ]

    sections = []
    for meal_type, label, emoji in type_config:
        meals = (
            db.query(Meal)
            .filter(Meal.meal_type == meal_type)
            .order_by(Meal.name)
            .all()
        )

        if meals:
            pool_meals = [
                PoolMeal(
                    id=m.id,
                    name=m.name,
                    nev=m.nev,
                    meal_type=m.meal_type,
                    cuisine=m.cuisine,
                    has_meat=m.has_meat,
                    is_vegetarian=m.is_vegetarian,
                    default_portions=m.default_portions,
                    keeps_days=m.keeps_days,
                    seasonality=m.seasonality,
                    effort_level=m.effort_level,
                    good_for_batch=m.good_for_batch,
                    reheats_well=m.reheats_well,
                    kid_friendly=m.kid_friendly,
                    typical_day=m.typical_day,
                )
                for m in meals
            ]
            sections.append(PoolSection(meal_type=meal_type, label=label, emoji=emoji, meals=pool_meals))

    return sections


def get_seasonal_suggestions(db: Session, limit: int = 6) -> list[PoolMeal]:
    """Get seasonal meal suggestions."""
    month = date.today().month
    if month in [12, 1, 2]:
        season = "winter"
    elif month in [3, 4, 5]:
        season = "spring"
    elif month in [6, 7, 8]:
        season = "summer"
    else:
        season = "autumn"

    meals = (
        db.query(Meal)
        .filter(Meal.seasonality == season)
        .limit(limit)
        .all()
    )

    # If not enough seasonal, fill with year_round soups/stews
    if len(meals) < limit:
        extra = (
            db.query(Meal)
            .filter(Meal.meal_type == "soup", Meal.seasonality == "year_round")
            .limit(limit - len(meals))
            .all()
        )
        meals.extend(extra)

    return [
        PoolMeal(
            id=m.id,
            name=m.name,
            nev=m.nev,
            meal_type=m.meal_type,
            cuisine=m.cuisine,
            has_meat=m.has_meat,
            is_vegetarian=m.is_vegetarian,
            default_portions=m.default_portions,
            keeps_days=m.keeps_days,
            seasonality=m.seasonality,
            effort_level=m.effort_level,
            good_for_batch=m.good_for_batch,
            reheats_well=m.reheats_well,
            kid_friendly=m.kid_friendly,
            typical_day=m.typical_day,
        )
        for m in meals
    ]


def get_recently_used(db: Session, limit: int = 8) -> list[PoolMeal]:
    """Get recently used meals from last 4 weeks."""
    four_weeks_ago = date.today() - timedelta(weeks=4)

    # Get meal IDs used in recent plans
    recent_meal_ids = (
        db.query(PlanMeal.meal_id)
        .join(WeeklyPlan)
        .filter(WeeklyPlan.start_date >= four_weeks_ago)
        .group_by(PlanMeal.meal_id)
        .order_by(func.count(PlanMeal.id).desc())
        .limit(limit)
        .all()
    )

    meal_ids = [m[0] for m in recent_meal_ids if m[0]]
    if not meal_ids:
        return []

    meals = db.query(Meal).filter(Meal.id.in_(meal_ids)).all()

    return [
        PoolMeal(
            id=m.id,
            name=m.name,
            nev=m.nev,
            meal_type=m.meal_type,
            cuisine=m.cuisine,
            has_meat=m.has_meat,
            is_vegetarian=m.is_vegetarian,
            default_portions=m.default_portions,
            keeps_days=m.keeps_days,
            seasonality=m.seasonality,
            effort_level=m.effort_level,
            good_for_batch=m.good_for_batch,
            reheats_well=m.reheats_well,
            kid_friendly=m.kid_friendly,
            typical_day=m.typical_day,
        )
        for m in meals
    ]


@router.get("/current", response_model=BoardData)
def get_current_week_board(db: Session = Depends(get_db)) -> BoardData:
    """Get board data for the current week."""
    year, week = get_current_week()
    return get_week_board(year, week, db)


@router.get("/search")
def search_meals(q: str = "", db: Session = Depends(get_db)) -> list[PoolMeal]:
    """Search meals for the pool sidebar."""
    if not q or len(q) < 2:
        return []

    pattern = f"%{q}%"
    meals = (
        db.query(Meal)
        .filter(Meal.name.ilike(pattern) | Meal.nev.ilike(pattern))
        .order_by(Meal.name)
        .limit(20)
        .all()
    )

    return [
        PoolMeal(
            id=m.id,
            name=m.name,
            nev=m.nev,
            meal_type=m.meal_type,
            cuisine=m.cuisine,
            has_meat=m.has_meat,
            is_vegetarian=m.is_vegetarian,
            default_portions=m.default_portions,
            keeps_days=m.keeps_days,
            seasonality=m.seasonality,
            effort_level=m.effort_level,
            good_for_batch=m.good_for_batch,
            reheats_well=m.reheats_well,
            kid_friendly=m.kid_friendly,
            typical_day=m.typical_day,
        )
        for m in meals
    ]


# ============== MONTHLY VIEW ==============

def get_month_dates(year: int, month: int) -> list[date]:
    """Get all dates to display for a month (includes padding from adjacent months)."""
    import calendar

    # Get the first day of the month and its weekday
    first_day = date(year, month, 1)
    first_weekday = first_day.weekday()  # 0=Monday

    # Calculate how many days to include from previous month
    start_date = first_day - timedelta(days=first_weekday)

    # Get last day of month
    _, last_day_num = calendar.monthrange(year, month)
    last_day = date(year, month, last_day_num)
    last_weekday = last_day.weekday()

    # Calculate how many days to include from next month (fill to Sunday)
    days_after = 6 - last_weekday
    end_date = last_day + timedelta(days=days_after)

    # Generate all dates
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    return dates


@router.get("/month/{year}/{month}", response_model=MonthBoardData)
def get_month_board(year: int, month: int, db: Session = Depends(get_db)) -> MonthBoardData:
    """Get board data for a specific month."""
    import calendar

    month_name = calendar.month_name[month]
    dates = get_month_dates(year, month)

    # Get all plans that overlap with this date range
    start_date = dates[0]
    end_date = dates[-1]

    # Get all plan meals in the date range by joining through plans
    plan_meals_by_date: dict[date, dict[str, PlanMeal]] = {}

    # Find all weeks that overlap with our date range
    start_iso = start_date.isocalendar()
    end_iso = end_date.isocalendar()

    # Query all potentially relevant plans
    plans = (
        db.query(WeeklyPlan)
        .filter(
            WeeklyPlan.start_date >= start_date - timedelta(days=7),
            WeeklyPlan.start_date <= end_date,
        )
        .all()
    )

    # Build lookup of plan meals by date
    for plan in plans:
        for pm in plan.plan_meals:
            # Skip plan meals without a day or slot assigned
            if pm.day_of_week is None or pm.meal_slot is None:
                continue
            meal_date = plan.start_date + timedelta(days=pm.day_of_week)
            if start_date <= meal_date <= end_date:
                if meal_date not in plan_meals_by_date:
                    plan_meals_by_date[meal_date] = {}
                plan_meals_by_date[meal_date][pm.meal_slot] = pm

    # Build week rows
    weeks: list[MonthWeekRow] = []
    slot_types = ["breakfast", "lunch", "dinner", "snack"]

    for i in range(0, len(dates), 7):
        week_dates = dates[i:i+7]
        if not week_dates:
            continue

        iso = week_dates[0].isocalendar()
        week_number = iso[1]
        week_year = iso[0]

        days: list[MonthDay] = []
        for d in week_dates:
            slots = {}
            for slot_type in slot_types:
                slot = BoardSlot()
                if d in plan_meals_by_date and slot_type in plan_meals_by_date[d]:
                    pm = plan_meals_by_date[d][slot_type]
                    if pm.meal:
                        slot = BoardSlot(
                            plan_meal_id=pm.id,
                            meal=MealResponse.model_validate(pm.meal),
                            is_leftover=pm.is_leftover,
                            portions_remaining=pm.portions_remaining,
                            chain_id=pm.chain_id,
                        )
                slots[slot_type] = slot

            days.append(MonthDay(
                day=d.day,
                date=d,
                day_of_week=d.weekday(),
                is_current_month=(d.month == month),
                slots=slots,
            ))

        weeks.append(MonthWeekRow(
            week_number=week_number,
            year=week_year,
            days=days,
        ))

    month_data = BoardMonth(
        year=year,
        month=month,
        month_name=month_name,
        weeks=weeks,
    )

    # Reuse pool building functions
    pool = build_meal_pool(db)
    suggestions = get_seasonal_suggestions(db)
    recently_used = get_recently_used(db)

    return MonthBoardData(
        month=month_data,
        pool=pool,
        suggestions=suggestions,
        recently_used=recently_used,
    )


@router.get("/month/current", response_model=MonthBoardData)
def get_current_month_board(db: Session = Depends(get_db)) -> MonthBoardData:
    """Get board data for the current month."""
    today = date.today()
    return get_month_board(today.year, today.month, db)


# ============== SLOT OPERATIONS ==============

@router.post("/slot")
def assign_meal_to_slot(data: SlotAssignRequest, db: Session = Depends(get_db)) -> dict:
    """Assign a meal to a slot, optionally creating a leftover chain."""
    from uuid import uuid4

    # Get or create the weekly plan
    plan = (
        db.query(WeeklyPlan)
        .filter(WeeklyPlan.year == data.year, WeeklyPlan.week_number == data.week)
        .first()
    )

    if not plan:
        start_date, _ = get_week_dates(data.year, data.week)
        plan = WeeklyPlan(
            year=data.year,
            week_number=data.week,
            start_date=start_date,
        )
        db.add(plan)
        db.flush()

    # Get the meal
    meal = db.query(Meal).filter(Meal.id == data.meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    # Check if slot is already occupied
    existing = (
        db.query(PlanMeal)
        .filter(
            PlanMeal.plan_id == plan.id,
            PlanMeal.day_of_week == data.day_of_week,
            PlanMeal.meal_slot == data.meal_slot,
        )
        .first()
    )

    if existing:
        # Remove existing meal from slot
        db.delete(existing)
        db.flush()

    # Create plan meal(s)
    created_slots = []
    chain_id = str(uuid4()) if data.create_chain and data.chain_days > 1 else None
    start_date, _ = get_week_dates(data.year, data.week)
    cooked_date = start_date + timedelta(days=data.day_of_week)

    for i in range(data.chain_days):
        day = data.day_of_week + i
        if day > 6:  # Don't go past Sunday
            break

        plan_meal = PlanMeal(
            plan_id=plan.id,
            meal_id=data.meal_id,
            day_of_week=day,
            meal_slot=data.meal_slot,
            is_leftover=(i > 0),
            portions_remaining=meal.default_portions - i if chain_id else None,
            chain_id=chain_id,
            cooked_on_date=cooked_date if chain_id else None,
        )
        db.add(plan_meal)
        db.flush()

        created_slots.append({
            "id": plan_meal.id,
            "day": day,
            "is_leftover": plan_meal.is_leftover,
            "portions": plan_meal.portions_remaining,
        })

    db.commit()

    return {
        "success": True,
        "chain_id": chain_id,
        "slots": created_slots,
        "plan_id": plan.id,
    }


@router.put("/slot/{plan_meal_id}")
def update_slot(
    plan_meal_id: int,
    day_of_week: int | None = None,
    meal_slot: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """Update a slot (move to different day/slot)."""
    plan_meal = db.query(PlanMeal).filter(PlanMeal.id == plan_meal_id).first()
    if not plan_meal:
        raise HTTPException(status_code=404, detail="Slot not found")

    # Check if target is occupied
    if day_of_week is not None or meal_slot is not None:
        target_day = day_of_week if day_of_week is not None else plan_meal.day_of_week
        target_slot = meal_slot if meal_slot is not None else plan_meal.meal_slot

        existing = (
            db.query(PlanMeal)
            .filter(
                PlanMeal.plan_id == plan_meal.plan_id,
                PlanMeal.day_of_week == target_day,
                PlanMeal.meal_slot == target_slot,
                PlanMeal.id != plan_meal_id,
            )
            .first()
        )

        if existing:
            # Swap positions
            existing.day_of_week = plan_meal.day_of_week
            existing.meal_slot = plan_meal.meal_slot

        plan_meal.day_of_week = target_day
        plan_meal.meal_slot = target_slot

    db.commit()

    return {"success": True, "id": plan_meal.id}


@router.delete("/slot/{plan_meal_id}")
def delete_slot(
    plan_meal_id: int,
    break_chain: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    """Remove a meal from a slot.

    If break_chain is True and the meal is part of a chain,
    removes the entire chain. Otherwise just removes this slot.
    """
    plan_meal = db.query(PlanMeal).filter(PlanMeal.id == plan_meal_id).first()
    if not plan_meal:
        raise HTTPException(status_code=404, detail="Slot not found")

    chain_id = plan_meal.chain_id
    removed_count = 1

    if chain_id and break_chain:
        # Remove entire chain
        chain_meals = (
            db.query(PlanMeal)
            .filter(PlanMeal.chain_id == chain_id)
            .all()
        )
        removed_count = len(chain_meals)
        for pm in chain_meals:
            db.delete(pm)
    else:
        db.delete(plan_meal)

    db.commit()

    return {"success": True, "chain_id": chain_id, "removed_count": removed_count}


# ============== CHAIN OPERATIONS ==============

@router.post("/chain/{chain_id}/extend")
def extend_chain(chain_id: str, days: int = 1, db: Session = Depends(get_db)) -> dict:
    """Extend a leftover chain by adding more days."""
    # Get chain meals
    chain_meals = (
        db.query(PlanMeal)
        .filter(PlanMeal.chain_id == chain_id)
        .order_by(PlanMeal.day_of_week.desc())
        .all()
    )

    if not chain_meals:
        raise HTTPException(status_code=404, detail="Chain not found")

    last_meal = chain_meals[0]
    meal = db.query(Meal).filter(Meal.id == last_meal.meal_id).first()

    # Calculate new portions
    current_last_portions = last_meal.portions_remaining or 1
    if current_last_portions <= 1:
        raise HTTPException(status_code=400, detail="No portions remaining to extend")

    created = []
    for i in range(1, days + 1):
        new_day = last_meal.day_of_week + i
        if new_day > 6:
            break

        new_portions = current_last_portions - i
        if new_portions < 1:
            break

        # Check if slot is free
        existing = (
            db.query(PlanMeal)
            .filter(
                PlanMeal.plan_id == last_meal.plan_id,
                PlanMeal.day_of_week == new_day,
                PlanMeal.meal_slot == last_meal.meal_slot,
            )
            .first()
        )

        if existing:
            break

        new_plan_meal = PlanMeal(
            plan_id=last_meal.plan_id,
            meal_id=last_meal.meal_id,
            day_of_week=new_day,
            meal_slot=last_meal.meal_slot,
            is_leftover=True,
            portions_remaining=new_portions,
            chain_id=chain_id,
            cooked_on_date=last_meal.cooked_on_date,
        )
        db.add(new_plan_meal)
        created.append(new_day)

    db.commit()

    return {"success": True, "extended_days": created}


@router.post("/chain/{chain_id}/shrink")
def shrink_chain(chain_id: str, db: Session = Depends(get_db)) -> dict:
    """Remove the last day from a leftover chain."""
    chain_meals = (
        db.query(PlanMeal)
        .filter(PlanMeal.chain_id == chain_id)
        .order_by(PlanMeal.day_of_week.desc())
        .all()
    )

    if not chain_meals:
        raise HTTPException(status_code=404, detail="Chain not found")

    if len(chain_meals) <= 1:
        raise HTTPException(status_code=400, detail="Cannot shrink chain with only one meal")

    # Remove the last one (highest day_of_week)
    last_meal = chain_meals[0]
    db.delete(last_meal)
    db.commit()

    return {"success": True, "removed_day": last_meal.day_of_week}


@router.delete("/chain/{chain_id}")
def delete_chain(chain_id: str, db: Session = Depends(get_db)) -> dict:
    """Delete an entire leftover chain."""
    chain_meals = (
        db.query(PlanMeal)
        .filter(PlanMeal.chain_id == chain_id)
        .all()
    )

    if not chain_meals:
        raise HTTPException(status_code=404, detail="Chain not found")

    count = len(chain_meals)
    for pm in chain_meals:
        db.delete(pm)

    db.commit()

    return {"success": True, "removed_count": count}
