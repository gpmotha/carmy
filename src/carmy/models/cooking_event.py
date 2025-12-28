"""CookingEvent model for v2 planning."""

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from carmy.models.database import Base

if TYPE_CHECKING:
    from carmy.models.meal import Meal
    from carmy.models.meal_slot import MealSlot
    from carmy.models.week_skeleton import WeekSkeleton


class CookingEventType(str, Enum):
    """Types of cooking events."""

    BIG_COOK = "big_cook"   # Saturday-style, makes lots
    MID_WEEK = "mid_week"   # Tuesday/Wednesday cook
    QUICK = "quick"         # Fast meal (Friday burgers)
    SPECIAL = "special"     # Birthday dinner, guest meal
    REGULAR = "regular"     # Default


class CookingEvent(Base):
    """A cooking session that produces food for multiple days."""

    __tablename__ = "cooking_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_skeleton_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("week_skeletons.id", ondelete="CASCADE"), nullable=False
    )
    meal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("meals.id", ondelete="CASCADE"), nullable=False
    )

    # When is this cooked?
    cook_date: Mapped[date] = mapped_column(Date, nullable=False)
    cook_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # "morning", "afternoon", "evening", None

    # How much food does this produce?
    serves_days: Mapped[int] = mapped_column(Integer, default=1)
    # 1 = eaten same day
    # 2-4 = leftovers for following days

    portions: Mapped[int] = mapped_column(Integer, default=4)
    # How many servings

    # Effort classification (copied from meal, but can override)
    effort_level: Mapped[str] = mapped_column(String(20), default="medium")

    # Event type
    event_type: Mapped[str] = mapped_column(String(20), default="regular")

    # Actual vs planned (for learning)
    was_made: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    # True = made as planned
    # False = skipped/substituted
    # None = not yet known

    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # 1-5 family rating after eating

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    week_skeleton: Mapped["WeekSkeleton"] = relationship("WeekSkeleton", back_populates="cooking_events")
    meal: Mapped["Meal"] = relationship("Meal", back_populates="cooking_events")
    meal_slots: Mapped[list["MealSlot"]] = relationship("MealSlot", back_populates="cooking_event")

    __table_args__ = (
        Index("idx_cooking_events_date", "cook_date"),
        Index("idx_cooking_events_week", "week_skeleton_id"),
    )

    def __repr__(self) -> str:
        return f"<CookingEvent(id={self.id}, date={self.cook_date}, meal_id={self.meal_id})>"
