"""Meal and MealIngredient models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from carmy.models.database import Base

if TYPE_CHECKING:
    from carmy.models.cooking_event import CookingEvent
    from carmy.models.meal_slot import MealSlot
    from carmy.models.plan import PlanMeal
    from carmy.models.recipe import Recipe


class MealType(str, Enum):
    """Types of meals."""

    SOUP = "soup"
    MAIN_COURSE = "main_course"
    PASTA = "pasta"
    SALAD = "salad"
    DESSERT = "dessert"
    BREAKFAST = "breakfast"
    APPETIZER = "appetizer"
    SPREAD = "spread"
    BEVERAGE = "beverage"
    CONDIMENT = "condiment"
    DINNER = "dinner"
    MEAT = "meat"
    PASTRY = "pastry"
    VEGAN = "vegan"


class Cuisine(str, Enum):
    """Cuisine types."""

    HUNGARIAN = "hungarian"
    ITALIAN = "italian"
    FRENCH = "french"
    INDIAN = "indian"
    MIDDLE_EASTERN = "middle_eastern"
    AMERICAN = "american"
    ASIAN = "asian"
    INTERNATIONAL = "international"
    AUSTRIAN = "austrian"
    BALKAN = "balkan"
    BELGIAN = "belgian"
    BRITISH = "british"
    CUBAN = "cuban"
    GERMAN = "german"
    GREEK = "greek"
    MEXICAN = "mexican"


class Seasonality(str, Enum):
    """Seasonal availability."""

    YEAR_ROUND = "year_round"
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


class Difficulty(str, Enum):
    """Cooking difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"


class EffortLevel(str, Enum):
    """Cooking effort levels for v2 planning."""

    NONE = "none"      # No cooking (leftover, sandwich, takeout)
    QUICK = "quick"    # < 30 min, minimal prep
    MEDIUM = "medium"  # 30-60 min, moderate effort
    BIG = "big"        # > 60 min, major cooking session


class TypicalDay(str, Enum):
    """Typical cooking days in the week."""

    FRIDAY = "friday"      # Fun food day
    SATURDAY = "saturday"  # Big cook day
    TUESDAY = "tuesday"    # Mid-week cook day


class Meal(Base):
    """A meal that can be part of a weekly plan."""

    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nev: Mapped[str] = mapped_column(String(255), nullable=False)  # Hungarian name
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # English name
    meal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cuisine: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prep_time_minutes: Mapped[int] = mapped_column(Integer, default=0)
    cook_time_minutes: Mapped[int] = mapped_column(Integer, default=0)
    difficulty: Mapped[str] = mapped_column(String(20), default="easy")
    seasonality: Mapped[str] = mapped_column(String(20), default="year_round")
    is_vegetarian: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vegan: Mapped[bool] = mapped_column(Boolean, default=False)
    has_meat: Mapped[bool] = mapped_column(Boolean, default=False)
    servings: Mapped[int] = mapped_column(Integer, default=4)
    default_portions: Mapped[int] = mapped_column(Integer, default=1)
    keeps_days: Mapped[int] = mapped_column(Integer, default=1)

    # v2 planning attributes
    effort_level: Mapped[str] = mapped_column(String(20), default="medium")
    good_for_batch: Mapped[bool] = mapped_column(Boolean, default=False)
    reheats_well: Mapped[bool] = mapped_column(Boolean, default=True)
    kid_friendly: Mapped[bool] = mapped_column(Boolean, default=True)
    typical_day: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    image_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    ingredients: Mapped[list["MealIngredient"]] = relationship(
        "MealIngredient", back_populates="meal", cascade="all, delete-orphan"
    )
    recipe: Mapped[Optional["Recipe"]] = relationship(
        "Recipe", back_populates="meal", uselist=False, cascade="all, delete-orphan"
    )
    plan_meals: Mapped[list["PlanMeal"]] = relationship("PlanMeal", back_populates="meal")

    # v2 relationships
    cooking_events: Mapped[list["CookingEvent"]] = relationship("CookingEvent", back_populates="meal")
    meal_slots: Mapped[list["MealSlot"]] = relationship("MealSlot", back_populates="meal")

    __table_args__ = (
        Index("idx_meals_type", "meal_type"),
        Index("idx_meals_cuisine", "cuisine"),
    )

    def __repr__(self) -> str:
        return f"<Meal(id={self.id}, name='{self.name}', nev='{self.nev}')>"

    @property
    def flavor_bases(self) -> list[str]:
        """Get flavor base ingredients for taste diversity checking."""
        return [ing.ingredient for ing in self.ingredients if ing.is_flavor_base]

    @property
    def total_time_minutes(self) -> int:
        """Total preparation and cooking time."""
        return self.prep_time_minutes + self.cook_time_minutes


class MealIngredient(Base):
    """An ingredient for a meal, including flavor base tagging."""

    __tablename__ = "meal_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meal_id: Mapped[int] = mapped_column(Integer, ForeignKey("meals.id", ondelete="CASCADE"))
    ingredient: Mapped[str] = mapped_column(String(100), nullable=False)
    is_flavor_base: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    meal: Mapped["Meal"] = relationship("Meal", back_populates="ingredients")

    __table_args__ = (Index("idx_meal_ingredients_meal", "meal_id"),)

    def __repr__(self) -> str:
        return f"<MealIngredient(meal_id={self.meal_id}, ingredient='{self.ingredient}')>"
