"""Recipe model for detailed cooking instructions."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from carmy.models.database import Base

if TYPE_CHECKING:
    from carmy.models.meal import Meal


class Recipe(Base):
    """Detailed recipe instructions for a meal."""

    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("meals.id", ondelete="CASCADE"), unique=True
    )
    instructions_hu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Hungarian
    instructions_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # English
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tips: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    meal: Mapped["Meal"] = relationship("Meal", back_populates="recipe")

    def __repr__(self) -> str:
        return f"<Recipe(id={self.id}, meal_id={self.meal_id})>"
