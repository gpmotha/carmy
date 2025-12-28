"""Pydantic schemas for plans."""

from datetime import date

from pydantic import BaseModel

from carmy.api.schemas.meal import MealResponse


class PlanMealResponse(BaseModel):
    """Schema for a meal in a plan."""

    id: int
    meal: MealResponse | None
    day_of_week: int | None = None
    meal_slot: str | None = None
    is_leftover: bool
    portions_remaining: int | None = None
    chain_id: str | None = None
    cooked_on_date: date | None = None

    class Config:
        from_attributes = True


class PlanResponse(BaseModel):
    """Schema for a weekly plan response."""

    id: int
    year: int
    week_number: int
    start_date: date
    plan_meals: list[PlanMealResponse]

    class Config:
        from_attributes = True


class PlanSummary(BaseModel):
    """Schema for plan list summary."""

    id: int
    year: int
    week_number: int
    start_date: date
    meal_count: int
    soup_count: int
    main_count: int

    class Config:
        from_attributes = True
