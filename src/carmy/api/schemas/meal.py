"""Pydantic schemas for meals."""

from pydantic import BaseModel


class MealBase(BaseModel):
    """Base meal schema with common fields."""

    name: str
    nev: str
    meal_type: str
    cuisine: str | None = None
    has_meat: bool = False
    is_vegetarian: bool = False
    is_vegan: bool = False
    calories: int | None = None
    prep_time_minutes: int | None = None
    seasonality: str | None = None
    flavor_base: str | None = None
    default_portions: int = 1
    keeps_days: int = 1
    # v2 planning attributes
    effort_level: str = "medium"
    good_for_batch: bool = False
    reheats_well: bool = True
    kid_friendly: bool = True
    typical_day: str | None = None


class MealCreate(MealBase):
    """Schema for creating a new meal."""

    pass


class MealUpdate(BaseModel):
    """Schema for updating a meal (all fields optional)."""

    name: str | None = None
    nev: str | None = None
    meal_type: str | None = None
    cuisine: str | None = None
    has_meat: bool | None = None
    is_vegetarian: bool | None = None
    is_vegan: bool | None = None
    calories: int | None = None
    prep_time_minutes: int | None = None
    seasonality: str | None = None
    flavor_base: str | None = None
    default_portions: int | None = None
    keeps_days: int | None = None
    # v2 planning attributes
    effort_level: str | None = None
    good_for_batch: bool | None = None
    reheats_well: bool | None = None
    kid_friendly: bool | None = None
    typical_day: str | None = None


class MealResponse(MealBase):
    """Schema for meal response."""

    id: int

    class Config:
        from_attributes = True
