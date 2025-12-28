"""HTML page routes for Carmy Web UI."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from carmy import __version__
from carmy.api.deps import get_db
from carmy.models.meal import Meal
from carmy.models.plan import WeeklyPlan
from carmy.services.analytics import AnalyticsService
from carmy.services.generator import GeneratorConfig, PlanGenerator
from carmy.services.rules_engine import RulesEngine
from carmy.services.seasonality import SeasonalityService, get_current_season

router = APIRouter()

# Templates setup
from pathlib import Path
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def _get_special_date_icon(event_type: str) -> str:
    """Get icon for a special date event type."""
    icons = {
        "birthday": "&#127874;",  # Birthday cake
        "holiday": "&#127878;",   # Christmas tree
        "guests": "&#128101;",    # People
        "party": "&#127881;",     # Party popper
        "away": "&#9992;",        # Airplane
        "name_day": "&#127873;",  # Gift
        "eating_out": "&#127869;", # Plate with cutlery
    }
    return icons.get(event_type, "&#128197;")  # Default calendar


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


# ============== HOME ==============

@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    """Home page with dashboard."""
    year, week = get_current_week()
    season = get_current_season()

    # Get current plan
    current_plan_data = None
    plan = db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.year == year, WeeklyPlan.week_number == week
        )
    ).scalar_one_or_none()

    if plan:
        soups = [pm.meal for pm in plan.plan_meals if pm.meal and pm.meal.meal_type == "soup"]
        mains = [pm.meal for pm in plan.plan_meals if pm.meal and pm.meal.meal_type in ("main_course", "pasta", "dinner")]
        current_plan_data = {"soups": soups, "mains": mains}

    # Get stats
    total_meals = db.execute(select(func.count(Meal.id))).scalar() or 0
    total_plans = db.execute(select(func.count(WeeklyPlan.id))).scalar() or 0
    soups_count = db.execute(select(func.count(Meal.id)).where(Meal.meal_type == "soup")).scalar() or 0
    mains_count = db.execute(
        select(func.count(Meal.id)).where(Meal.meal_type.in_(["main_course", "pasta", "dinner"]))
    ).scalar() or 0

    # Recent plans
    recent_plans = db.execute(
        select(WeeklyPlan)
        .order_by(WeeklyPlan.year.desc(), WeeklyPlan.week_number.desc())
        .limit(5)
    ).scalars().all()

    recent_plans_data = []
    for p in recent_plans:
        meals = [pm for pm in p.plan_meals if pm.meal]
        recent_plans_data.append({
            "year": p.year,
            "week_number": p.week_number,
            "start_date": p.start_date,
            "meal_count": len(meals),
            "soup_count": len([pm for pm in meals if pm.meal.meal_type == "soup"]),
            "main_count": len([pm for pm in meals if pm.meal.meal_type in ("main_course", "pasta", "dinner")]),
        })

    return templates.TemplateResponse("index.html", {
        "request": request,
        "version": __version__,
        "current_week": {"year": year, "week": week},
        "current_plan": current_plan_data,
        "season": season,
        "stats": {
            "total_meals": total_meals,
            "total_plans": total_plans,
            "soups": soups_count,
            "mains": mains_count,
        },
        "recent_plans": recent_plans_data,
    })


# ============== MEALS ==============

@router.get("/meals", response_class=HTMLResponse)
def meals_list(
    request: Request,
    search: str = Query(None),
    meal_type: str = Query(None),
    cuisine: str = Query(None),
    vegetarian: bool = Query(None),
    has_meat: bool = Query(None),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    """Meals listing page."""
    per_page = 50
    offset = (page - 1) * per_page

    # Build query
    query = select(Meal)

    if search:
        pattern = f"%{search}%"
        query = query.where(Meal.name.ilike(pattern) | Meal.nev.ilike(pattern))
    if meal_type:
        query = query.where(Meal.meal_type == meal_type)
    if cuisine:
        query = query.where(Meal.cuisine == cuisine)
    if vegetarian:
        query = query.where(Meal.is_vegetarian == True)
    if has_meat:
        query = query.where(Meal.has_meat == True)

    # Get total count
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    # Get paginated results
    meals = db.execute(
        query.order_by(Meal.name).offset(offset).limit(per_page)
    ).scalars().all()

    # Get filter options
    meal_types = db.execute(
        select(Meal.meal_type).distinct().where(Meal.meal_type.isnot(None)).order_by(Meal.meal_type)
    ).scalars().all()

    cuisines = db.execute(
        select(Meal.cuisine).distinct().where(Meal.cuisine.isnot(None)).order_by(Meal.cuisine)
    ).scalars().all()

    return templates.TemplateResponse("meals/list.html", {
        "request": request,
        "version": __version__,
        "meals": meals,
        "total_meals": total,
        "page": page,
        "total_pages": (total + per_page - 1) // per_page,
        "meal_types": meal_types,
        "cuisines": cuisines,
        "filters": {
            "search": search,
            "meal_type": meal_type,
            "cuisine": cuisine,
            "vegetarian": vegetarian,
            "has_meat": has_meat,
        },
    })


@router.get("/meals/{meal_id}", response_class=HTMLResponse)
def meal_detail(request: Request, meal_id: int, db: Session = Depends(get_db)):
    """Meal detail page."""
    meal = db.get(Meal, meal_id)
    if not meal:
        return RedirectResponse("/meals", status_code=302)

    # Get usage history
    analytics = AnalyticsService(db)
    history = analytics.get_meal_history(meal_id)

    # Get seasonality scores
    seasonality_service = SeasonalityService()
    seasonality = {}
    for season in ["winter", "spring", "summer", "autumn"]:
        score = seasonality_service.score_meal(meal, season)
        seasonality[season] = score.score

    return templates.TemplateResponse("meals/detail.html", {
        "request": request,
        "version": __version__,
        "meal": meal,
        "history": history,
        "seasonality": seasonality,
    })


# ============== PLANS ==============

@router.get("/plans", response_class=HTMLResponse)
def plans_list(
    request: Request,
    year: int = Query(None),
    db: Session = Depends(get_db),
):
    """Plans listing page."""
    query = select(WeeklyPlan).order_by(
        WeeklyPlan.year.desc(), WeeklyPlan.week_number.desc()
    )

    if year:
        query = query.where(WeeklyPlan.year == year)

    query = query.limit(50)
    plans = db.execute(query).scalars().all()

    # Build plan summaries
    plans_data = []
    for p in plans:
        meals = [pm for pm in p.plan_meals if pm.meal]
        plans_data.append({
            "id": p.id,
            "year": p.year,
            "week_number": p.week_number,
            "start_date": p.start_date,
            "meal_count": len(meals),
            "soup_count": len([pm for pm in meals if pm.meal.meal_type == "soup"]),
            "main_count": len([pm for pm in meals if pm.meal.meal_type in ("main_course", "pasta", "dinner")]),
        })

    # Get available years
    years = db.execute(
        select(WeeklyPlan.year).distinct().order_by(WeeklyPlan.year.desc())
    ).scalars().all()

    total_plans = db.execute(select(func.count(WeeklyPlan.id))).scalar() or 0

    return templates.TemplateResponse("plans/list.html", {
        "request": request,
        "version": __version__,
        "plans": plans_data,
        "years": years,
        "selected_year": year,
        "total_plans": total_plans,
    })


@router.get("/plans/generate", response_class=HTMLResponse)
def plans_generate_form(request: Request, db: Session = Depends(get_db)):
    """Plan generation form."""
    year, week = get_current_week()
    next_week = week + 1
    next_year = year
    if next_week > 52:
        next_week = 1
        next_year += 1

    season = get_current_season()

    return templates.TemplateResponse("plans/generate.html", {
        "request": request,
        "version": __version__,
        "default_week": next_week,
        "default_year": next_year,
        "season": season,
        "preview": None,
    })


@router.post("/plans/generate", response_class=HTMLResponse)
def plans_generate_submit(
    request: Request,
    week: int = Form(...),
    year: int = Form(...),
    randomness: float = Form(0.3),
    save: bool = Form(False),
    db: Session = Depends(get_db),
):
    """Handle plan generation form submission."""
    season = get_current_season()

    # Check if plan exists
    existing = db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.year == year, WeeklyPlan.week_number == week
        )
    ).scalar_one_or_none()

    if existing:
        return templates.TemplateResponse("plans/generate.html", {
            "request": request,
            "version": __version__,
            "default_week": week,
            "default_year": year,
            "season": season,
            "preview": None,
            "error": f"Plan for week {week}, {year} already exists.",
        })

    # Generate plan
    start_date = get_week_start(year, week)
    config = GeneratorConfig(randomness=randomness)
    generator = PlanGenerator(db, config)
    plan = generator.generate(year, week, start_date)

    preview = {
        "year": plan.year,
        "week_number": plan.week_number,
        "season": plan.season,
        "soups": plan.soups,
        "main_courses": plan.main_courses,
        "validation": plan.validation,
        "saved": False,
    }

    if save:
        generator.save_plan(plan)
        preview["saved"] = True

    return templates.TemplateResponse("plans/generate.html", {
        "request": request,
        "version": __version__,
        "default_week": week,
        "default_year": year,
        "season": season,
        "preview": preview,
    })


@router.get("/plans/{year}/{week}", response_class=HTMLResponse)
def plan_detail(request: Request, year: int, week: int, db: Session = Depends(get_db)):
    """Plan detail page."""
    plan = db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.year == year, WeeklyPlan.week_number == week
        )
    ).scalar_one_or_none()

    if not plan:
        return RedirectResponse("/plans", status_code=302)

    # Categorize meals
    soups = [pm for pm in plan.plan_meals if pm.meal and pm.meal.meal_type == "soup"]
    mains = [pm for pm in plan.plan_meals if pm.meal and pm.meal.meal_type in ("main_course", "pasta", "dinner")]
    others = [pm for pm in plan.plan_meals if pm.meal and pm.meal.meal_type not in ("soup", "main_course", "pasta", "dinner")]

    meat_count = len([pm for pm in plan.plan_meals if pm.meal and pm.meal.has_meat])

    # Validate plan
    rules = RulesEngine()
    validation = rules.validate(plan)

    # Navigation (prev/next week)
    prev_week = db.execute(
        select(WeeklyPlan)
        .where(
            (WeeklyPlan.year < year) |
            ((WeeklyPlan.year == year) & (WeeklyPlan.week_number < week))
        )
        .order_by(WeeklyPlan.year.desc(), WeeklyPlan.week_number.desc())
        .limit(1)
    ).scalar_one_or_none()

    next_week = db.execute(
        select(WeeklyPlan)
        .where(
            (WeeklyPlan.year > year) |
            ((WeeklyPlan.year == year) & (WeeklyPlan.week_number > week))
        )
        .order_by(WeeklyPlan.year, WeeklyPlan.week_number)
        .limit(1)
    ).scalar_one_or_none()

    return templates.TemplateResponse("plans/detail.html", {
        "request": request,
        "version": __version__,
        "plan": plan,
        "soups": soups,
        "mains": mains,
        "others": others,
        "meat_count": meat_count,
        "validation": {
            "is_valid": validation.is_valid,
            "violations": validation.violations,
        },
        "prev_week": {"year": prev_week.year, "week": prev_week.week_number} if prev_week else None,
        "next_week": {"year": next_week.year, "week": next_week.week_number} if next_week else None,
    })


# ============== ANALYTICS ==============

@router.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request, db: Session = Depends(get_db)):
    """Analytics dashboard page."""
    service = AnalyticsService(db)
    report = service.generate_full_report()

    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "version": __version__,
        "report": report,
    })


# ============== PLANNING BOARD ==============

@router.get("/board", response_class=HTMLResponse)
def board_current(request: Request, db: Session = Depends(get_db)):
    """Planning board for current week."""
    year, week = get_current_week()
    return board_week(request, year, week, db)


@router.get("/board/week/{year}/{week}", response_class=HTMLResponse)
def board_week(request: Request, year: int, week: int, db: Session = Depends(get_db)):
    """Planning board for a specific week."""
    from carmy.api.routes.board import get_week_board, get_week_dates

    # Get board data
    board_data = get_week_board(year, week, db)

    # Calculate prev/next week
    prev_week = week - 1
    prev_year = year
    if prev_week < 1:
        prev_week = 52
        prev_year -= 1

    next_week = week + 1
    next_year = year
    if next_week > 52:
        next_week = 1
        next_year += 1

    return templates.TemplateResponse("board/week.html", {
        "request": request,
        "version": __version__,
        "week": board_data.week,
        "pool": board_data.pool,
        "suggestions": board_data.suggestions,
        "recently_used": board_data.recently_used,
        "today": date.today(),
        "prev_year": prev_year,
        "prev_week": prev_week,
        "next_year": next_year,
        "next_week": next_week,
    })


# ============== MONTHLY PLANNING BOARD ==============

@router.get("/board/month", response_class=HTMLResponse)
def board_month_current(request: Request, db: Session = Depends(get_db)):
    """Planning board for current month."""
    today = date.today()
    return board_month(request, today.year, today.month, db)


@router.get("/board/month/{year}/{month}", response_class=HTMLResponse)
def board_month(request: Request, year: int, month: int, db: Session = Depends(get_db)):
    """Planning board for a specific month."""
    from carmy.api.routes.board import get_month_board

    # Get board data
    board_data = get_month_board(year, month, db)

    # Calculate prev/next month
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1

    return templates.TemplateResponse("board/month.html", {
        "request": request,
        "version": __version__,
        "month": board_data.month,
        "pool": board_data.pool,
        "suggestions": board_data.suggestions,
        "recently_used": board_data.recently_used,
        "today": date.today(),
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    })


# ============== V2 MONTH PLANNING ==============

@router.get("/month/setup", response_class=HTMLResponse)
def month_setup_current(request: Request, db: Session = Depends(get_db)):
    """Month setup wizard for current month."""
    today = date.today()
    # Start with next month if we're past the 15th
    if today.day > 15:
        month = today.month + 1
        year = today.year
        if month > 12:
            month = 1
            year += 1
    else:
        month = today.month
        year = today.year
    return month_setup(request, year, month, db)


@router.get("/month/setup/{year}/{month}", response_class=HTMLResponse)
def month_setup(request: Request, year: int, month: int, db: Session = Depends(get_db)):
    """Month setup wizard for a specific month."""
    import calendar
    import json
    from sqlalchemy import select
    from carmy.models.month_plan import MonthPlan
    from carmy.services.theme_settings import list_themes, MonthSettingsV2

    # Get month name
    month_name = calendar.month_name[month]
    days_in_month = calendar.monthrange(year, month)[1]

    # Check for existing plan
    existing_plan = db.execute(
        select(MonthPlan).where(MonthPlan.year == year, MonthPlan.month == month)
    ).scalar_one_or_none()

    # Get settings (from existing plan or defaults)
    if existing_plan and existing_plan.settings:
        settings = MonthSettingsV2.from_dict(existing_plan.settings)
    else:
        settings = MonthSettingsV2()

    # Get special dates for this plan
    special_dates = []
    if existing_plan:
        special_dates = [
            {
                "id": sd.id,
                "date": sd.date.isoformat(),
                "name": sd.name,
                "event_type": sd.event_type,
                "affects_cooking": sd.affects_cooking,
            }
            for sd in existing_plan.special_dates
        ]

    # Get available themes
    themes = list_themes()

    return templates.TemplateResponse("month/setup.html", {
        "request": request,
        "version": __version__,
        "year": year,
        "month": month,
        "month_name": month_name,
        "days_in_month": days_in_month,
        "existing_plan": existing_plan,
        "settings": settings,
        "special_dates": special_dates,
        "themes": themes,
    })


@router.post("/month/setup/{year}/{month}", response_class=HTMLResponse)
def month_setup_submit(
    request: Request,
    year: int,
    month: int,
    theme: str = Form(""),
    meat_level: int = Form(50),
    fish_level: int = Form(30),
    veggie_level: int = Form(50),
    new_recipes: int = Form(30),
    cuisine_balance: int = Form(50),
    lent_mode: bool = Form(False),
    batch_cooking: bool = Form(False),
    sales_aware: bool = Form(True),
    big_cook_days: list[int] = Form([]),
    mid_week_cook_days: list[int] = Form([]),
    fun_food_days: list[int] = Form([]),
    soups_per_week: int = Form(2),
    main_courses_per_week: int = Form(4),
    max_meat_per_week: int = Form(3),
    special_dates_json: str = Form("[]"),
    db: Session = Depends(get_db),
):
    """Handle month setup form submission and generate plan."""
    import json
    from datetime import datetime
    from sqlalchemy import select
    from carmy.models.month_plan import MonthPlan, SpecialDate
    from carmy.services.theme_settings import MonthSettingsV2
    from carmy.services.month_orchestrator import MonthOrchestrator

    # Build settings
    settings = MonthSettingsV2(
        meat_level=meat_level / 100.0,
        fish_level=fish_level / 100.0,
        veggie_level=veggie_level / 100.0,
        new_recipes=new_recipes / 100.0,
        cuisine_balance=cuisine_balance / 100.0,
        lent_mode=lent_mode,
        batch_cooking=batch_cooking,
        sales_aware=sales_aware,
        big_cook_days=big_cook_days or [5],  # Default Saturday
        mid_week_cook_days=mid_week_cook_days or [1, 2],  # Default Tue, Wed
        fun_food_days=fun_food_days or [4],  # Default Friday
        soups_per_week=soups_per_week,
        main_courses_per_week=main_courses_per_week,
        max_meat_per_week=max_meat_per_week,
    )

    # Get or create month plan
    plan = db.execute(
        select(MonthPlan).where(MonthPlan.year == year, MonthPlan.month == month)
    ).scalar_one_or_none()

    if not plan:
        from carmy.models.month_plan import get_season_for_month
        plan = MonthPlan(
            year=year,
            month=month,
            theme=theme or None,
            season=get_season_for_month(month),
            settings=settings.to_dict(),
        )
        db.add(plan)
    else:
        plan.theme = theme or None
        plan.settings = settings.to_dict()

    db.flush()

    # Handle special dates
    try:
        special_dates = json.loads(special_dates_json)
    except json.JSONDecodeError:
        special_dates = []

    # Remove existing special dates
    for sd in plan.special_dates:
        db.delete(sd)

    # Add new special dates
    for sd_data in special_dates:
        sd = SpecialDate(
            month_plan_id=plan.id,
            date=datetime.strptime(sd_data["date"], "%Y-%m-%d").date(),
            event_type=sd_data.get("event_type", "other"),
            name=sd_data.get("name", ""),
            affects_cooking=sd_data.get("affects_cooking", True),
        )
        db.add(sd)

    db.commit()

    # Generate the month plan with special dates
    from carmy.services.month_orchestrator import SpecialDateInfo

    # Convert special dates to SpecialDateInfo objects
    special_date_infos = [
        SpecialDateInfo(
            date=sd.date,
            event_type=sd.event_type,
            name=sd.name or "",
            affects_cooking=sd.affects_cooking,
        )
        for sd in plan.special_dates
    ]

    orchestrator = MonthOrchestrator(db)
    generated = orchestrator.generate_month(
        year, month, settings, theme or None, special_date_infos
    )
    orchestrator.save_month(generated, plan)

    # Redirect to skeleton view
    return RedirectResponse(f"/month/{year}/{month}", status_code=303)


# ============== TODAY VIEW ==============

@router.get("/today", response_class=HTMLResponse)
def today_view(request: Request, db: Session = Depends(get_db)):
    """What's for dinner today? The quick glance view."""
    from sqlalchemy.orm import selectinload
    from carmy.models.week_skeleton import WeekSkeleton
    from carmy.models.meal_slot import MealSlot

    today = date.today()
    current_hour = __import__('datetime').datetime.now().hour
    year, week = get_current_week()

    # Determine meal period and greeting
    if current_hour < 11:
        meal_period = "Breakfast"
        greeting = "Good morning! Here's what's planned for today."
    elif current_hour < 15:
        meal_period = "Lunch"
        greeting = "Lunchtime! Here's what's on the menu."
    elif current_hour < 18:
        meal_period = "Dinner"
        greeting = "Afternoon! Time to think about dinner."
    else:
        meal_period = "Dinner"
        greeting = "Good evening! Here's tonight's plan."

    # Get current week skeleton with meal slots
    skeleton = db.execute(
        select(WeekSkeleton)
        .where(WeekSkeleton.year == year, WeekSkeleton.week_number == week)
        .options(selectinload(WeekSkeleton.meal_slots).selectinload(MealSlot.meal))
    ).scalar_one_or_none()

    has_plan = skeleton is not None and len(skeleton.meal_slots) > 0

    dinner = None
    lunch = None
    soup = None

    if has_plan:
        # Get today's slots
        today_slots = [s for s in skeleton.meal_slots if s.date == today]

        for slot in today_slots:
            slot_data = {
                "id": slot.id,
                "meal_name": slot.meal.name if slot.meal else None,
                "meal_type": slot.meal.meal_type if slot.meal else None,
                "source": slot.source,
                "leftover_day": slot.leftover_day,
                "status": slot.status,
            }

            if slot.notes == "Soup":
                soup = slot_data
            elif slot.meal_time == "dinner":
                dinner = slot_data
            elif slot.meal_time == "lunch":
                lunch = slot_data

    # Get upcoming days (next 3 days)
    upcoming = []
    if skeleton:
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i in range(1, 4):
            future_date = today + timedelta(days=i)
            if future_date <= skeleton.end_date:
                day_slots = [s for s in skeleton.meal_slots if s.date == future_date]
                if day_slots:
                    meals = []
                    for slot in day_slots:
                        meals.append({
                            "name": slot.meal.name if slot.meal else None,
                            "source": slot.source,
                            "leftover_day": slot.leftover_day,
                            "is_soup": slot.notes == "Soup",
                        })
                    upcoming.append({
                        "date": future_date,
                        "day_name": day_names[future_date.weekday()],
                        "meals": meals,
                    })

    return templates.TemplateResponse("today.html", {
        "request": request,
        "version": __version__,
        "today": today,
        "year": year,
        "week": week,
        "month": today.month,
        "meal_period": meal_period,
        "greeting": greeting,
        "has_plan": has_plan,
        "dinner": dinner,
        "lunch": lunch,
        "soup": soup,
        "upcoming": upcoming,
    })


# ============== V2 WEEK VIEW ==============

@router.get("/week", response_class=HTMLResponse)
def week_view_current(request: Request, db: Session = Depends(get_db)):
    """Week view for current week."""
    year, week = get_current_week()
    return week_view(request, year, week, db)


@router.get("/week/{year}/{week}", response_class=HTMLResponse)
def week_view(request: Request, year: int, week: int, db: Session = Depends(get_db)):
    """Day-by-day view of a materialized week."""
    from sqlalchemy.orm import selectinload
    from carmy.models.week_skeleton import WeekSkeleton
    from carmy.models.cooking_event import CookingEvent
    from carmy.models.meal_slot import MealSlot
    from carmy.services.week_materializer import WeekMaterializer

    today = date.today()
    current_year, current_week = get_current_week()

    # Calculate prev/next week
    prev_week = week - 1
    prev_year = year
    if prev_week < 1:
        prev_week = 52
        prev_year -= 1

    next_week = week + 1
    next_year = year
    if next_week > 52:
        next_week = 1
        next_year += 1

    # Get week skeleton with all relationships
    skeleton = db.execute(
        select(WeekSkeleton)
        .where(WeekSkeleton.year == year, WeekSkeleton.week_number == week)
        .options(
            selectinload(WeekSkeleton.cooking_events).selectinload(CookingEvent.meal),
            selectinload(WeekSkeleton.meal_slots).selectinload(MealSlot.meal),
        )
    ).scalar_one_or_none()

    if not skeleton:
        # No skeleton found
        return templates.TemplateResponse("week/view.html", {
            "request": request,
            "version": __version__,
            "year": year,
            "week_number": week,
            "start_date": get_week_start(year, week),
            "end_date": get_week_start(year, week) + timedelta(days=6),
            "skeleton": None,
            "has_slots": False,
            "cooking_events_count": 0,
            "days": [],
            "summary": {},
            "month": get_week_start(year, week).month,
            "prev_year": prev_year,
            "prev_week": prev_week,
            "next_year": next_year,
            "next_week": next_week,
            "current_year": current_year,
            "current_week": current_week,
        })

    has_slots = len(skeleton.meal_slots) > 0

    # Get summary if we have slots
    summary = {}
    if has_slots:
        materializer = WeekMaterializer(db)
        summary = materializer.get_week_summary(skeleton)

    # Build day-by-day data
    days = []
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    current_date = skeleton.start_date
    while current_date <= skeleton.end_date:
        day_slots = [
            slot for slot in skeleton.meal_slots
            if slot.date == current_date
        ]

        # Sort slots: dinner first, then lunch, then by soup indicator
        day_slots.sort(key=lambda s: (
            0 if s.meal_time == "dinner" else 1,
            1 if s.notes == "Soup" else 0,
        ))

        # Build slot data
        slots_data = []
        for slot in day_slots:
            is_soup = slot.notes == "Soup"
            slots_data.append({
                "id": slot.id,
                "meal_time": slot.meal_time,
                "meal_name": slot.meal.name if slot.meal else None,
                "meal_type": slot.meal.meal_type if slot.meal else None,
                "source": slot.source,
                "leftover_day": slot.leftover_day,
                "status": slot.status,
                "is_soup": is_soup,
            })

        days.append({
            "date": current_date,
            "day_name": day_names[current_date.weekday()],
            "is_today": current_date == today,
            "slots": slots_data,
        })

        current_date += timedelta(days=1)

    return templates.TemplateResponse("week/view.html", {
        "request": request,
        "version": __version__,
        "year": year,
        "week_number": week,
        "start_date": skeleton.start_date,
        "end_date": skeleton.end_date,
        "skeleton": skeleton,
        "has_slots": has_slots,
        "cooking_events_count": len(skeleton.cooking_events),
        "days": days,
        "summary": summary,
        "month": skeleton.start_date.month,
        "prev_year": prev_year,
        "prev_week": prev_week,
        "next_year": next_year,
        "next_week": next_week,
        "current_year": current_year,
        "current_week": current_week,
    })


@router.get("/month/{year}/{month}", response_class=HTMLResponse)
def month_skeleton_view(request: Request, year: int, month: int, db: Session = Depends(get_db)):
    """View generated month skeleton with cooking events."""
    import calendar
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    from carmy.models.month_plan import MonthPlan
    from carmy.services.theme_settings import MonthSettingsV2, get_theme

    # Get month plan with all relationships
    plan = db.execute(
        select(MonthPlan)
        .options(joinedload(MonthPlan.week_skeletons))
        .where(MonthPlan.year == year, MonthPlan.month == month)
    ).unique().scalar_one_or_none()

    if not plan:
        # Redirect to setup if no plan exists
        return RedirectResponse(f"/month/setup/{year}/{month}", status_code=302)

    # Get month name
    month_name = calendar.month_name[month]

    # Get settings
    settings = MonthSettingsV2.from_dict(plan.settings or {})

    # Get theme info
    theme_info = get_theme(plan.theme) if plan.theme else None

    # Index special dates by date for quick lookup
    special_dates_by_date = {sd.date: sd for sd in plan.special_dates}

    # Build weeks data for display
    weeks_data = []
    for ws in sorted(plan.week_skeletons, key=lambda w: w.week_number):
        week_info = {
            "id": ws.id,
            "week_number": ws.week_number,
            "start_date": ws.start_date,
            "end_date": ws.end_date,
            "cooking_events": [],
        }

        # Get cooking events for this week
        for ce in ws.cooking_events:
            meal = ce.meal
            # Calculate day_of_week from cook_date (Monday = 0)
            day_of_week = ce.cook_date.weekday() if ce.cook_date else 0

            # Check if this is a special date
            special_date = special_dates_by_date.get(ce.cook_date)
            special_date_info = None
            if special_date:
                special_date_info = {
                    "name": special_date.name,
                    "event_type": special_date.event_type,
                    "icon": _get_special_date_icon(special_date.event_type),
                }

            event_info = {
                "id": ce.id,
                "day_of_week": day_of_week,
                "day_name": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day_of_week],
                "cook_date": ce.cook_date,
                "event_type": ce.event_type,
                "portions": ce.portions,
                "special_date": special_date_info,
                "meal": {
                    "id": meal.id,
                    "name": meal.name,
                    "nev": meal.nev,
                    "meal_type": meal.meal_type,
                    "has_meat": meal.has_meat,
                    "is_vegetarian": meal.is_vegetarian,
                } if meal else None,
            }
            week_info["cooking_events"].append(event_info)

        # Sort events by day
        week_info["cooking_events"].sort(key=lambda e: e["day_of_week"])
        weeks_data.append(week_info)

    # Calculate prev/next month
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1

    return templates.TemplateResponse("month/skeleton.html", {
        "request": request,
        "version": __version__,
        "year": year,
        "month": month,
        "month_name": month_name,
        "plan": plan,
        "settings": settings,
        "theme_info": theme_info,
        "weeks": weeks_data,
        "special_dates": plan.special_dates,
        "today": date.today(),
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    })
