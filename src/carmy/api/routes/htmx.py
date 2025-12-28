"""HTMX partial routes for Carmy Web UI."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import random

from carmy import __version__
from carmy.api.deps import get_db
from carmy.models.meal import Meal
from carmy.models.plan import PlanMeal, WeeklyPlan

router = APIRouter()

# Templates setup
from pathlib import Path
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ============== MEALS HTMX ==============

@router.get("/meals/search", response_class=HTMLResponse)
def htmx_meals_search(
    request: Request,
    search: str = Query(None),
    meal_type: str = Query(None),
    cuisine: str = Query(None),
    vegetarian: bool = Query(None),
    has_meat: bool = Query(None),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    """HTMX endpoint for live meal search."""
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

    return templates.TemplateResponse("meals/_grid.html", {
        "request": request,
        "meals": meals,
        "total_meals": total,
        "page": page,
        "total_pages": (total + per_page - 1) // per_page,
    })


@router.get("/meals/{meal_id}/edit", response_class=HTMLResponse)
def htmx_meal_edit_form(
    request: Request,
    meal_id: int,
    db: Session = Depends(get_db),
):
    """HTMX endpoint to get meal edit form."""
    meal = db.get(Meal, meal_id)
    if not meal:
        return HTMLResponse("<p>Meal not found</p>", status_code=404)

    # Get filter options
    meal_types = db.execute(
        select(Meal.meal_type).distinct().where(Meal.meal_type.isnot(None)).order_by(Meal.meal_type)
    ).scalars().all()

    cuisines = db.execute(
        select(Meal.cuisine).distinct().where(Meal.cuisine.isnot(None)).order_by(Meal.cuisine)
    ).scalars().all()

    return templates.TemplateResponse("meals/_details_edit.html", {
        "request": request,
        "meal": meal,
        "meal_types": meal_types,
        "cuisines": cuisines,
    })


@router.get("/meals/{meal_id}/view", response_class=HTMLResponse)
def htmx_meal_view(
    request: Request,
    meal_id: int,
    db: Session = Depends(get_db),
):
    """HTMX endpoint to get meal view (after canceling edit)."""
    meal = db.get(Meal, meal_id)
    if not meal:
        return HTMLResponse("<p>Meal not found</p>", status_code=404)

    html = templates.TemplateResponse("meals/_details_view.html", {
        "request": request,
        "meal": meal,
    })

    # Re-add the header with edit button
    content = f"""
    <header>
        <h3>Details
            <button class="btn-sm outline"
                    hx-get="/htmx/meals/{meal.id}/edit"
                    hx-target="#meal-details"
                    hx-swap="innerHTML">
                Edit
            </button>
        </h3>
    </header>
    """ + html.body.decode()

    return HTMLResponse(content)


@router.put("/meals/{meal_id}", response_class=HTMLResponse)
def htmx_meal_update(
    request: Request,
    meal_id: int,
    name: Annotated[str, Form()],
    nev: Annotated[str, Form()],
    meal_type: Annotated[str, Form()],
    cuisine: Annotated[str | None, Form()] = None,
    has_meat: Annotated[bool, Form()] = False,
    is_vegetarian: Annotated[bool, Form()] = False,
    calories: Annotated[int | None, Form()] = None,
    prep_time_minutes: Annotated[int | None, Form()] = None,
    db: Session = Depends(get_db),
):
    """HTMX endpoint to update a meal."""
    meal = db.get(Meal, meal_id)
    if not meal:
        return HTMLResponse("<p>Meal not found</p>", status_code=404)

    # Update meal
    meal.name = name
    meal.nev = nev
    meal.meal_type = meal_type
    meal.cuisine = cuisine if cuisine else None
    meal.has_meat = has_meat
    meal.is_vegetarian = is_vegetarian
    meal.calories = calories if calories else None
    meal.prep_time_minutes = prep_time_minutes if prep_time_minutes else None

    db.commit()
    db.refresh(meal)

    # Return the view template with success toast trigger
    content = f"""
    <header>
        <h3>Details
            <button class="btn-sm outline"
                    hx-get="/htmx/meals/{meal.id}/edit"
                    hx-target="#meal-details"
                    hx-swap="innerHTML">
                Edit
            </button>
        </h3>
    </header>
    """ + templates.TemplateResponse("meals/_details_view.html", {
        "request": request,
        "meal": meal,
    }).body.decode()

    response = HTMLResponse(content)
    # Add HX-Trigger header to show toast
    response.headers["HX-Trigger"] = json.dumps({
        "showToast": {"message": "Meal updated successfully!", "type": "success"}
    })

    return response


# ============== PLANS HTMX ==============

# ============== BOARD HTMX ==============

@router.get("/board/search", response_class=HTMLResponse)
def htmx_board_search(
    request: Request,
    q: str = Query(""),
    db: Session = Depends(get_db),
):
    """HTMX endpoint for board pool search."""
    if not q or len(q) < 2:
        # Return empty state
        return HTMLResponse('<p style="color: var(--muted-color); text-align: center; padding: 1rem;">Type at least 2 characters to search</p>')

    pattern = f"%{q}%"
    meals = db.execute(
        select(Meal)
        .where(Meal.name.ilike(pattern) | Meal.nev.ilike(pattern))
        .order_by(Meal.name)
        .limit(20)
    ).scalars().all()

    if not meals:
        return HTMLResponse('<p style="color: var(--muted-color); text-align: center; padding: 1rem;">No meals found</p>')

    # Build HTML for search results
    html_parts = ['<div class="pool-section"><div class="pool-section-header"><span>Search Results</span><span>' + str(len(meals)) + '</span></div><div class="pool-items">']

    for meal in meals:
        portions_badge = f'<span class="portions-badge">[{meal.default_portions}]</span>' if meal.default_portions > 1 else ''
        html_parts.append(f'''
            <div class="pool-meal" draggable="true" data-meal-id="{meal.id}" data-portions="{meal.default_portions}">
                <span>{meal.name}</span>
                {portions_badge}
            </div>
        ''')

    html_parts.append('</div></div>')

    return HTMLResponse(''.join(html_parts))


# ============== PLANS HTMX ==============

@router.post("/plans/{plan_id}/meals/{plan_meal_id}/regenerate", response_class=HTMLResponse)
def htmx_regenerate_meal_slot(
    request: Request,
    plan_id: int,
    plan_meal_id: int,
    db: Session = Depends(get_db),
):
    """HTMX endpoint to swap a single meal in a plan."""
    plan_meal = db.get(PlanMeal, plan_meal_id)
    if not plan_meal or plan_meal.plan_id != plan_id:
        return HTMLResponse("<p>Not found</p>", status_code=404)

    old_meal = plan_meal.meal
    if not old_meal:
        return HTMLResponse("<p>No meal to swap</p>", status_code=400)

    # Get current plan meals to avoid
    plan = db.get(WeeklyPlan, plan_id)
    current_meal_ids = {pm.meal_id for pm in plan.plan_meals if pm.meal}

    # Get meals of the same type
    candidates = db.execute(
        select(Meal)
        .where(Meal.meal_type == old_meal.meal_type)
        .where(Meal.id.notin_(current_meal_ids))
    ).scalars().all()

    if not candidates:
        response = HTMLResponse(templates.TemplateResponse("plans/_meal_card.html", {
            "request": request,
            "pm": plan_meal,
            "plan_id": plan_id,
        }).body.decode())
        response.headers["HX-Trigger"] = json.dumps({
            "showToast": {"message": "No alternative meals available", "type": "error"}
        })
        return response

    # Pick a random replacement
    new_meal = random.choice(candidates)
    plan_meal.meal_id = new_meal.id
    db.commit()
    db.refresh(plan_meal)

    response = HTMLResponse(templates.TemplateResponse("plans/_meal_card.html", {
        "request": request,
        "pm": plan_meal,
        "plan_id": plan_id,
    }).body.decode())

    response.headers["HX-Trigger"] = json.dumps({
        "showToast": {"message": f"Swapped to: {new_meal.name}", "type": "success"}
    })

    return response
