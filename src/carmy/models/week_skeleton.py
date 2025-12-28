"""WeekSkeleton model for v2 planning."""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from carmy.models.database import Base

if TYPE_CHECKING:
    from carmy.models.cooking_event import CookingEvent
    from carmy.models.meal_slot import MealSlot
    from carmy.models.month_plan import MonthPlan


class WeekStatus(str, Enum):
    """Status of a week skeleton."""

    SKELETON = "skeleton"           # High-level only
    MATERIALIZED = "materialized"   # Daily plan generated
    IN_PROGRESS = "in_progress"     # Current week
    COMPLETED = "completed"         # Done


class WeekSkeleton(Base):
    """High-level weekly plan. Contains cooking events, not individual meals."""

    __tablename__ = "week_skeletons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    month_plan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("month_plans.id", ondelete="SET NULL"), nullable=True
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)  # ISO week number
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="skeleton")

    # Week-level notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    month_plan: Mapped[Optional["MonthPlan"]] = relationship("MonthPlan", back_populates="week_skeletons")
    cooking_events: Mapped[list["CookingEvent"]] = relationship(
        "CookingEvent",
        back_populates="week_skeleton",
        cascade="all, delete-orphan"
    )
    meal_slots: Mapped[list["MealSlot"]] = relationship(
        "MealSlot",
        back_populates="week_skeleton",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("year", "week_number", name="unique_week_skeleton"),
        Index("idx_week_skeletons_year_week", "year", "week_number"),
        Index("idx_week_skeletons_dates", "start_date", "end_date"),
    )

    def __repr__(self) -> str:
        return f"<WeekSkeleton(id={self.id}, year={self.year}, week={self.week_number})>"
