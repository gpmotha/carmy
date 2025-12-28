"""Pydantic schemas for WeekSkeleton, CookingEvent, and MealSlot."""

from datetime import date, datetime

from pydantic import BaseModel, Field


# ============== COOKING EVENT SCHEMAS ==============

class CookingEventBase(BaseModel):
    """Base schema for cooking event."""

    meal_id: int
    cook_date: date
    cook_time: str | None = Field(None, description="morning, afternoon, evening")
    serves_days: int = Field(1, ge=1, le=7, description="How many days this feeds")
    portions: int = Field(4, ge=1)
    effort_level: str = Field("medium", description="none, quick, medium, big")
    event_type: str = Field("regular", description="big_cook, mid_week, quick, special, regular")
    notes: str | None = None


class CookingEventCreate(CookingEventBase):
    """Schema for creating a cooking event."""

    pass


class CookingEventUpdate(BaseModel):
    """Schema for updating a cooking event."""

    meal_id: int | None = None
    cook_date: date | None = None
    cook_time: str | None = None
    serves_days: int | None = None
    portions: int | None = None
    effort_level: str | None = None
    event_type: str | None = None
    was_made: bool | None = None
    rating: int | None = Field(None, ge=1, le=5)
    notes: str | None = None


class CookingEventResponse(CookingEventBase):
    """Schema for cooking event response."""

    id: int
    week_skeleton_id: int
    was_made: bool | None
    rating: int | None
    meal_name: str | None = None
    meal_nev: str | None = None

    class Config:
        from_attributes = True


# ============== MEAL SLOT SCHEMAS ==============

class MealSlotBase(BaseModel):
    """Base schema for meal slot."""

    date: date
    meal_time: str = Field(..., description="breakfast, lunch, dinner, snack")
    meal_id: int | None = None
    source: str = Field("fresh", description="fresh, leftover, light, eat_out, skip")
    cooking_event_id: int | None = None
    leftover_day: int | None = Field(None, ge=1, description="Day number of leftover")
    notes: str | None = None


class MealSlotCreate(MealSlotBase):
    """Schema for creating a meal slot."""

    pass


class MealSlotUpdate(BaseModel):
    """Schema for updating a meal slot."""

    meal_id: int | None = None
    source: str | None = None
    cooking_event_id: int | None = None
    leftover_day: int | None = None
    status: str | None = None
    notes: str | None = None


class MealSlotResponse(MealSlotBase):
    """Schema for meal slot response."""

    id: int
    week_skeleton_id: int
    status: str
    meal_name: str | None = None
    meal_nev: str | None = None

    class Config:
        from_attributes = True


# ============== WEEK SKELETON SCHEMAS ==============

class WeekSkeletonBase(BaseModel):
    """Base schema for week skeleton."""

    year: int
    week_number: int = Field(..., ge=1, le=53)
    start_date: date
    end_date: date
    notes: str | None = None


class WeekSkeletonCreate(BaseModel):
    """Schema for creating a week skeleton."""

    year: int
    week_number: int = Field(..., ge=1, le=53)
    month_plan_id: int | None = None
    notes: str | None = None


class WeekSkeletonUpdate(BaseModel):
    """Schema for updating a week skeleton."""

    month_plan_id: int | None = None
    status: str | None = None
    notes: str | None = None


class WeekSkeletonSummary(BaseModel):
    """Summary schema for week skeleton listing."""

    id: int
    year: int
    week_number: int
    start_date: date
    end_date: date
    status: str
    month_plan_id: int | None
    cooking_event_count: int = 0
    meal_slot_count: int = 0

    class Config:
        from_attributes = True


class WeekSkeletonResponse(WeekSkeletonBase):
    """Full schema for week skeleton response."""

    id: int
    month_plan_id: int | None
    status: str
    created_at: datetime
    updated_at: datetime
    cooking_events: list[CookingEventResponse] = []
    meal_slots: list[MealSlotResponse] = []

    class Config:
        from_attributes = True


# ============== COOKING RHYTHM SCHEMAS ==============

class CookingRhythmResponse(BaseModel):
    """Schema for cooking rhythm response."""

    id: int
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    day_name: str
    cook_probability: float
    typical_effort: str | None
    typical_types: list[str] = []
    confidence: float
    calculated_at: datetime

    class Config:
        from_attributes = True
