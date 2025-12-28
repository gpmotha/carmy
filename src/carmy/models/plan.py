"""Weekly plan and plan meal models."""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from carmy.models.database import Base

if TYPE_CHECKING:
    from carmy.models.meal import Meal


class MealSlot(str, Enum):
    """Time slots for meals during the day."""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class WeeklyPlan(Base):
    """A weekly meal plan."""

    __tablename__ = "weekly_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    plan_meals: Mapped[list["PlanMeal"]] = relationship(
        "PlanMeal", back_populates="plan", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_plans_year_week", "year", "week_number", unique=True),)

    def __repr__(self) -> str:
        return f"<WeeklyPlan(year={self.year}, week={self.week_number})>"

    @property
    def soups(self) -> list["PlanMeal"]:
        """Get all soup entries in this plan."""
        return [pm for pm in self.plan_meals if pm.meal and pm.meal.meal_type == "soup"]

    @property
    def main_courses(self) -> list["PlanMeal"]:
        """Get all main course entries in this plan."""
        return [pm for pm in self.plan_meals if pm.meal and pm.meal.meal_type == "main_course"]

    @property
    def soup_count(self) -> int:
        """Count unique soups in this plan."""
        unique_soups = {pm.meal_id for pm in self.soups if not pm.is_leftover}
        return len(unique_soups)

    @property
    def main_course_count(self) -> int:
        """Count unique main courses in this plan."""
        unique_mains = {pm.meal_id for pm in self.main_courses if not pm.is_leftover}
        return len(unique_mains)


class PlanMeal(Base):
    """A meal assignment within a weekly plan."""

    __tablename__ = "plan_meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("weekly_plans.id", ondelete="CASCADE")
    )
    meal_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("meals.id"), nullable=True
    )
    day_of_week: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 0=Monday, 6=Sunday
    meal_slot: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_leftover: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Leftover chain tracking
    portions_remaining: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chain_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # UUID
    cooked_on_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    plan: Mapped["WeeklyPlan"] = relationship("WeeklyPlan", back_populates="plan_meals")
    meal: Mapped[Optional["Meal"]] = relationship("Meal", back_populates="plan_meals")

    __table_args__ = (Index("idx_plan_meals_plan", "plan_id"),)

    def __repr__(self) -> str:
        day = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][self.day_of_week] if self.day_of_week is not None else "?"
        return f"<PlanMeal(plan_id={self.plan_id}, day={day}, slot={self.meal_slot})>"

    @property
    def day_name(self) -> str:
        """Get the day name."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if self.day_of_week is not None and 0 <= self.day_of_week <= 6:
            return days[self.day_of_week]
        return "Unknown"
