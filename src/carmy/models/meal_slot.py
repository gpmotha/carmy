"""MealSlot model for v2 planning."""

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from carmy.models.database import Base

if TYPE_CHECKING:
    from carmy.models.cooking_event import CookingEvent
    from carmy.models.meal import Meal
    from carmy.models.week_skeleton import WeekSkeleton


class MealTime(str, Enum):
    """Meal times in a day."""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class MealSource(str, Enum):
    """Source of a meal in a slot."""

    FRESH = "fresh"         # Cooked that day
    LEFTOVER = "leftover"   # From earlier cooking event
    LIGHT = "light"         # No cooking, simple food
    EAT_OUT = "eat_out"     # Restaurant/takeaway
    SKIP = "skip"           # Not eating this meal


class SlotStatus(str, Enum):
    """Status of a meal slot."""

    PLANNED = "planned"         # In the plan
    CONFIRMED = "confirmed"     # User confirmed
    COMPLETED = "completed"     # Meal was eaten
    SKIPPED = "skipped"         # Didn't happen
    SUBSTITUTED = "substituted" # Replaced with something else


class MealSlot(Base):
    """A specific meal on a specific day (what you actually eat)."""

    __tablename__ = "meal_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_skeleton_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("week_skeletons.id", ondelete="CASCADE"), nullable=False
    )

    # When is this eaten?
    date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_time: Mapped[str] = mapped_column(String(20), nullable=False)
    # "breakfast", "lunch", "dinner", "snack"

    # What is eaten? (optional - could be eating out)
    meal_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("meals.id", ondelete="SET NULL"), nullable=True
    )

    # Source of this meal
    source: Mapped[str] = mapped_column(String(20), default="fresh")
    # "fresh" = cooked that day
    # "leftover" = from earlier cooking event
    # "light" = no cooking, simple food
    # "eat_out" = restaurant/takeaway
    # "skip" = not eating this meal

    # If leftover, link to the cooking event
    cooking_event_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("cooking_events.id", ondelete="SET NULL"), nullable=True
    )

    # Day number of leftover (1 = first day, 2 = second day, etc.)
    leftover_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="planned")

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    week_skeleton: Mapped["WeekSkeleton"] = relationship("WeekSkeleton", back_populates="meal_slots")
    meal: Mapped[Optional["Meal"]] = relationship("Meal", back_populates="meal_slots")
    cooking_event: Mapped[Optional["CookingEvent"]] = relationship("CookingEvent", back_populates="meal_slots")

    __table_args__ = (
        UniqueConstraint("date", "meal_time", name="unique_meal_slot"),
        Index("idx_meal_slots_date", "date"),
        Index("idx_meal_slots_date_time", "date", "meal_time"),
        Index("idx_meal_slots_week", "week_skeleton_id"),
    )

    def __repr__(self) -> str:
        return f"<MealSlot(id={self.id}, date={self.date}, time={self.meal_time})>"
