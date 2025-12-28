"""CookingRhythm model for v2 planning - learned cooking patterns."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from carmy.models.database import Base


class CookingRhythm(Base):
    """Learned pattern of when the family cooks (derived from history)."""

    __tablename__ = "cooking_rhythm"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Which day of week? (0=Monday, 6=Sunday)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)

    # Probability this is a cooking day (0.0 - 1.0)
    cook_probability: Mapped[float] = mapped_column(Float, default=0.5)

    # Typical effort level on this day
    typical_effort: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # "big", "medium", "quick", None

    # Typical meal types for this day (stored as JSON list)
    typical_types: Mapped[list[Any]] = mapped_column(JSON, default=list)
    # ["fun_food"] for Friday, ["fozelek"] for Tuesday, etc.

    # Confidence (how much data supports this)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    # 0.0 = just guessing
    # 1.0 = very confident from data

    # When was this last calculated?
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_cooking_rhythm_day", "day_of_week"),
    )

    def __repr__(self) -> str:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = days[self.day_of_week] if 0 <= self.day_of_week <= 6 else "Unknown"
        return f"<CookingRhythm(day={day_name}, cook_prob={self.cook_probability:.2f})>"
