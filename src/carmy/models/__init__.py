"""SQLAlchemy models for Carmy."""

from carmy.models.database import Base, get_engine, get_session, init_db
from carmy.models.meal import Meal, MealIngredient
from carmy.models.plan import PlanMeal, WeeklyPlan
from carmy.models.recipe import Recipe

# v2 models
from carmy.models.month_plan import MonthPlan, SpecialDate
from carmy.models.week_skeleton import WeekSkeleton
from carmy.models.cooking_event import CookingEvent
from carmy.models.meal_slot import MealSlot
from carmy.models.cooking_rhythm import CookingRhythm

__all__ = [
    "Base",
    "get_engine",
    "get_session",
    "init_db",
    "Meal",
    "MealIngredient",
    "Recipe",
    "WeeklyPlan",
    "PlanMeal",
    # v2 models
    "MonthPlan",
    "SpecialDate",
    "WeekSkeleton",
    "CookingEvent",
    "MealSlot",
    "CookingRhythm",
]
