"""Pydantic schemas for MonthPlan and SpecialDate."""

from datetime import date as DateType, datetime
from typing import Any

from pydantic import BaseModel, Field


class SpecialDateBase(BaseModel):
    """Base schema for special dates."""

    date: DateType
    event_type: str = Field(..., description="birthday, name_day, guests, holiday, party, away")
    name: str | None = None
    affects_cooking: bool = True
    notes: str | None = None


class SpecialDateCreate(SpecialDateBase):
    """Schema for creating a special date."""

    pass


class SpecialDateUpdate(BaseModel):
    """Schema for updating a special date."""

    date: DateType | None = None
    event_type: str | None = None
    name: str | None = None
    affects_cooking: bool | None = None
    notes: str | None = None


class SpecialDateResponse(SpecialDateBase):
    """Schema for special date response."""

    id: int
    month_plan_id: int

    class Config:
        from_attributes = True


class MonthPlanSettings(BaseModel):
    """Settings for a month plan."""

    meat_level: float = Field(0.5, ge=0, le=1, description="0 = none, 1 = lots")
    fish_level: float = Field(0.3, ge=0, le=1, description="Higher = more fish")
    veggie_level: float = Field(0.5, ge=0, le=1)
    new_recipes: float = Field(0.3, ge=0, le=1, description="How many new things to try")
    cuisine_balance: float = Field(0.5, ge=0, le=1, description="0 = all Hungarian, 1 = all international")
    lent_mode: bool = False
    sales_aware: bool = True
    batch_cooking: bool = False


class MonthPlanBase(BaseModel):
    """Base schema for month plan."""

    year: int
    month: int = Field(..., ge=1, le=12)
    theme: str | None = Field(None, description="comfort, light, seafood, budget, guests, pantry_clearing, lent, none")
    season: str | None = Field(None, description="Auto-detected if not provided: winter, spring, summer, autumn")
    settings: dict[str, Any] = Field(default_factory=dict)


class MonthPlanCreate(MonthPlanBase):
    """Schema for creating a month plan."""

    special_dates: list[SpecialDateCreate] = Field(default_factory=list)


class MonthPlanUpdate(BaseModel):
    """Schema for updating a month plan."""

    theme: str | None = None
    season: str | None = None
    settings: dict[str, Any] | None = None
    status: str | None = None


class MonthPlanSummary(BaseModel):
    """Summary schema for month plan listing."""

    id: int
    year: int
    month: int
    theme: str | None
    season: str
    status: str
    week_count: int = 0
    special_date_count: int = 0

    class Config:
        from_attributes = True


class MonthPlanResponse(MonthPlanBase):
    """Full schema for month plan response."""

    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    special_dates: list[SpecialDateResponse] = []

    class Config:
        from_attributes = True
