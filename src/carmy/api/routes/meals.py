"""Meal API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from carmy.api.deps import get_db
from carmy.api.schemas.meal import MealCreate, MealResponse, MealUpdate
from carmy.models.meal import Meal

router = APIRouter()


@router.get("", response_model=list[MealResponse])
def list_meals(
    meal_type: str | None = Query(None, description="Filter by meal type"),
    cuisine: str | None = Query(None, description="Filter by cuisine"),
    has_meat: bool | None = Query(None, description="Filter by meat content"),
    is_vegetarian: bool | None = Query(None, description="Filter vegetarian meals"),
    search: str | None = Query(None, description="Search by name"),
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[Meal]:
    """List all meals with optional filters."""
    query = select(Meal)

    if meal_type:
        query = query.where(Meal.meal_type == meal_type)
    if cuisine:
        query = query.where(Meal.cuisine == cuisine)
    if has_meat is not None:
        query = query.where(Meal.has_meat == has_meat)
    if is_vegetarian is not None:
        query = query.where(Meal.is_vegetarian == is_vegetarian)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            Meal.name.ilike(search_pattern) | Meal.nev.ilike(search_pattern)
        )

    query = query.order_by(Meal.name).offset(offset).limit(limit)
    return list(db.execute(query).scalars().all())


@router.get("/types")
def list_meal_types(db: Session = Depends(get_db)) -> list[str]:
    """Get all unique meal types."""
    result = db.execute(select(Meal.meal_type).distinct().order_by(Meal.meal_type))
    return [r for r in result.scalars().all() if r]


@router.get("/cuisines")
def list_cuisines(db: Session = Depends(get_db)) -> list[str]:
    """Get all unique cuisines."""
    result = db.execute(select(Meal.cuisine).distinct().order_by(Meal.cuisine))
    return [r for r in result.scalars().all() if r]


@router.get("/{meal_id}", response_model=MealResponse)
def get_meal(meal_id: int, db: Session = Depends(get_db)) -> Meal:
    """Get a specific meal by ID."""
    meal = db.get(Meal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal


@router.post("", response_model=MealResponse, status_code=201)
def create_meal(meal_data: MealCreate, db: Session = Depends(get_db)) -> Meal:
    """Create a new meal."""
    meal = Meal(**meal_data.model_dump())
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


@router.put("/{meal_id}", response_model=MealResponse)
def update_meal(
    meal_id: int,
    meal_data: MealUpdate,
    db: Session = Depends(get_db),
) -> Meal:
    """Update an existing meal."""
    meal = db.get(Meal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    update_data = meal_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meal, field, value)

    db.commit()
    db.refresh(meal)
    return meal


@router.delete("/{meal_id}", status_code=204)
def delete_meal(meal_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a meal."""
    meal = db.get(Meal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    db.delete(meal)
    db.commit()
