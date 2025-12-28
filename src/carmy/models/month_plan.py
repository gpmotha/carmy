"""MonthPlan and SpecialDate models for v2 planning."""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from carmy.models.database import Base

if TYPE_CHECKING:
    from carmy.models.week_skeleton import WeekSkeleton


class MonthTheme(str, Enum):
    """Monthly planning themes."""

    COMFORT = "comfort"           # Hearty winter food
    LIGHT = "light"               # Healthy, fresh eating
    SEAFOOD = "seafood"           # Fish focus
    BUDGET = "budget"             # Cost-conscious
    GUESTS = "guests"             # Entertaining
    PANTRY = "pantry_clearing"    # Use what we have
    LENT = "lent"                 # Religious observance
    NONE = "none"                 # No theme


class PlanStatus(str, Enum):
    """Status of a plan."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


class Season(str, Enum):
    """Seasons for meal planning."""

    WINTER = "winter"   # Dec, Jan, Feb
    SPRING = "spring"   # Mar, Apr, May
    SUMMER = "summer"   # Jun, Jul, Aug
    AUTUMN = "autumn"   # Sep, Oct, Nov


def get_season_for_month(month: int) -> str:
    """Get the season for a given month (1-12)."""
    if month in (12, 1, 2):
        return Season.WINTER.value
    elif month in (3, 4, 5):
        return Season.SPRING.value
    elif month in (6, 7, 8):
        return Season.SUMMER.value
    else:
        return Season.AUTUMN.value


class MonthPlan(Base):
    """Monthly meal plan - the top-level planning entity."""

    __tablename__ = "month_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12

    # Theme (optional)
    theme: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Season (auto-detected from month, but can override)
    season: Mapped[str] = mapped_column(String(20), nullable=False)

    # User settings for this month (stored as JSON)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # {
    #   "meat_level": 0.5,      # 0 = none, 1 = lots
    #   "fish_level": 0.7,      # higher = more fish
    #   "veggie_level": 0.5,
    #   "new_recipes": 0.3,     # how many new things to try
    #   "cuisine_balance": 0.5, # 0 = all Hungarian, 1 = all international
    #   "lent_mode": false,
    #   "sales_aware": true,
    #   "batch_cooking": false
    # }

    # Status
    status: Mapped[str] = mapped_column(String(20), default="draft")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    week_skeletons: Mapped[list["WeekSkeleton"]] = relationship(
        "WeekSkeleton",
        back_populates="month_plan",
        cascade="all, delete-orphan"
    )
    special_dates: Mapped[list["SpecialDate"]] = relationship(
        "SpecialDate",
        back_populates="month_plan",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("year", "month", name="unique_month_plan"),
        Index("idx_month_plans_year_month", "year", "month"),
    )

    def __repr__(self) -> str:
        return f"<MonthPlan(id={self.id}, year={self.year}, month={self.month})>"


class EventType(str, Enum):
    """Types of special events."""

    BIRTHDAY = "birthday"
    NAME_DAY = "name_day"
    GUESTS = "guests"
    HOLIDAY = "holiday"
    PARTY = "party"
    AWAY = "away"


class SpecialDate(Base):
    """Special dates within a month (birthdays, guests, holidays)."""

    __tablename__ = "special_dates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    month_plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("month_plans.id", ondelete="CASCADE"))

    date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)

    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # "Anna's birthday", "Christmas", etc.

    affects_cooking: Mapped[bool] = mapped_column(default=True)
    # If true, Carmy will suggest special meals

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    month_plan: Mapped["MonthPlan"] = relationship("MonthPlan", back_populates="special_dates")

    __table_args__ = (
        Index("idx_special_dates_date", "date"),
    )

    def __repr__(self) -> str:
        return f"<SpecialDate(id={self.id}, date={self.date}, type={self.event_type})>"
