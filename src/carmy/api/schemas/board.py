"""Pydantic schemas for the planning board."""

from datetime import date

from pydantic import BaseModel

from carmy.api.schemas.meal import MealResponse


class BoardSlot(BaseModel):
    """A single slot on the board (day + meal type)."""

    plan_meal_id: int | None = None
    meal: MealResponse | None = None
    is_leftover: bool = False
    portions_remaining: int | None = None
    chain_id: str | None = None


class BoardDay(BaseModel):
    """A single day on the board with all slots."""

    day_of_week: int  # 0=Monday, 6=Sunday
    day_name: str
    date: date
    slots: dict[str, BoardSlot]  # breakfast, lunch, dinner, snack


class BoardWeek(BaseModel):
    """Complete week board data."""

    year: int
    week: int
    start_date: date
    end_date: date
    plan_id: int | None = None
    days: list[BoardDay]


class PoolMeal(BaseModel):
    """A meal in the sidebar pool."""

    id: int
    name: str
    nev: str
    meal_type: str
    cuisine: str | None = None
    has_meat: bool = False
    is_vegetarian: bool = False
    default_portions: int = 1
    keeps_days: int = 1
    seasonality: str | None = None
    # v2 planning attributes
    effort_level: str = "medium"
    good_for_batch: bool = False
    reheats_well: bool = True
    kid_friendly: bool = True
    typical_day: str | None = None


class PoolSection(BaseModel):
    """A section in the meal pool."""

    meal_type: str
    label: str
    emoji: str
    meals: list[PoolMeal]


class BoardData(BaseModel):
    """Full board response with week data and meal pool."""

    week: BoardWeek
    pool: list[PoolSection]
    suggestions: list[PoolMeal] = []
    recently_used: list[PoolMeal] = []


class SlotAssignRequest(BaseModel):
    """Request to assign a meal to a slot."""

    year: int
    week: int
    day_of_week: int
    meal_slot: str
    meal_id: int
    create_chain: bool = False
    chain_days: int = 1


class SlotUpdateRequest(BaseModel):
    """Request to update a slot (move, change portions)."""

    day_of_week: int | None = None
    meal_slot: str | None = None
    portions_remaining: int | None = None


# ============== MONTHLY VIEW SCHEMAS ==============


class MonthDay(BaseModel):
    """A single day in the monthly calendar."""

    day: int  # Day of month (1-31)
    date: date
    day_of_week: int  # 0=Monday, 6=Sunday
    is_current_month: bool = True
    slots: dict[str, BoardSlot]  # All 4 slot types


class MonthWeekRow(BaseModel):
    """A week row in the monthly calendar."""

    week_number: int  # ISO week number
    year: int
    days: list[MonthDay]  # 7 days (Mon-Sun)


class BoardMonth(BaseModel):
    """Complete month board data."""

    year: int
    month: int
    month_name: str
    weeks: list[MonthWeekRow]


class MonthBoardData(BaseModel):
    """Full monthly board response with month data and meal pool."""

    month: BoardMonth
    pool: list[PoolSection]
    suggestions: list[PoolMeal] = []
    recently_used: list[PoolMeal] = []
