"""Historical analysis service for meal planning."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from carmy.models.meal import Meal

from carmy.models.meal import Meal
from carmy.models.plan import PlanMeal, WeeklyPlan


@dataclass
class MealStats:
    """Statistics for a single meal."""

    meal_id: int
    name: str
    nev: str
    meal_type: str
    cuisine: str | None
    total_count: int
    last_used_date: date | None
    last_used_week: int | None
    last_used_year: int | None
    weeks_since_last_use: int | None

    @property
    def frequency_score(self) -> float:
        """Higher score = more frequently used."""
        return self.total_count

    @property
    def recency_score(self) -> float:
        """Higher score = more recently used (less desirable for rotation)."""
        if self.weeks_since_last_use is None:
            return 0.0  # Never used = most desirable
        return max(0, 10 - self.weeks_since_last_use)


@dataclass
class AnalyzerResult:
    """Result of historical analysis."""

    total_meals: int
    total_plans: int
    meal_stats: list[MealStats]
    most_used: list[MealStats]
    least_used: list[MealStats]
    never_used: list[MealStats]
    recently_used: list[MealStats]
    cuisine_distribution: dict[str, int]
    type_distribution: dict[str, int]


class HistoricalAnalyzer:
    """Analyzes historical meal plan data."""

    def __init__(self, session: Session):
        self.session = session

    def analyze(self, reference_date: date | None = None) -> AnalyzerResult:
        """Perform full historical analysis.

        Args:
            reference_date: Date to calculate recency from (defaults to today)
        """
        if reference_date is None:
            reference_date = date.today()

        meal_stats = self._calculate_meal_stats(reference_date)
        cuisine_dist = self._get_cuisine_distribution()
        type_dist = self._get_type_distribution()

        # Sort for different views
        by_frequency = sorted(meal_stats, key=lambda m: m.total_count, reverse=True)
        by_recency = sorted(
            [m for m in meal_stats if m.last_used_date],
            key=lambda m: m.last_used_date,
            reverse=True,
        )

        total_plans = self.session.execute(
            select(func.count(WeeklyPlan.id))
        ).scalar() or 0

        return AnalyzerResult(
            total_meals=len(meal_stats),
            total_plans=total_plans,
            meal_stats=meal_stats,
            most_used=by_frequency[:10],
            least_used=[m for m in reversed(by_frequency) if m.total_count > 0][:10],
            never_used=[m for m in meal_stats if m.total_count == 0],
            recently_used=by_recency[:10],
            cuisine_distribution=cuisine_dist,
            type_distribution=type_dist,
        )

    def _calculate_meal_stats(self, reference_date: date) -> list[MealStats]:
        """Calculate statistics for each meal."""
        # Get all meals
        meals = self.session.execute(select(Meal)).scalars().all()

        # Get usage counts
        usage_counts = dict(
            self.session.execute(
                select(PlanMeal.meal_id, func.count(PlanMeal.id))
                .where(PlanMeal.meal_id.isnot(None))
                .group_by(PlanMeal.meal_id)
            ).all()
        )

        # Get last used dates (via plan's start_date)
        last_used_query = (
            select(
                PlanMeal.meal_id,
                func.max(WeeklyPlan.start_date).label("last_date"),
                func.max(WeeklyPlan.week_number).label("last_week"),
                func.max(WeeklyPlan.year).label("last_year"),
            )
            .join(WeeklyPlan, PlanMeal.plan_id == WeeklyPlan.id)
            .where(PlanMeal.meal_id.isnot(None))
            .group_by(PlanMeal.meal_id)
        )
        last_used = {
            row[0]: (row[1], row[2], row[3])
            for row in self.session.execute(last_used_query).all()
        }

        # Calculate weeks since reference
        ref_iso = reference_date.isocalendar()
        ref_week_num = ref_iso[0] * 52 + ref_iso[1]

        stats = []
        for meal in meals:
            count = usage_counts.get(meal.id, 0)
            last_date, last_week, last_year = last_used.get(meal.id, (None, None, None))

            weeks_since = None
            if last_year and last_week:
                last_week_num = last_year * 52 + last_week
                weeks_since = ref_week_num - last_week_num

            stats.append(
                MealStats(
                    meal_id=meal.id,
                    name=meal.name,
                    nev=meal.nev,
                    meal_type=meal.meal_type,
                    cuisine=meal.cuisine,
                    total_count=count,
                    last_used_date=last_date,
                    last_used_week=last_week,
                    last_used_year=last_year,
                    weeks_since_last_use=weeks_since,
                )
            )

        return stats

    def _get_cuisine_distribution(self) -> dict[str, int]:
        """Get distribution of cuisines in historical plans."""
        results = self.session.execute(
            select(Meal.cuisine, func.count(PlanMeal.id))
            .join(PlanMeal, PlanMeal.meal_id == Meal.id)
            .where(Meal.cuisine.isnot(None))
            .group_by(Meal.cuisine)
            .order_by(func.count(PlanMeal.id).desc())
        ).all()
        return {cuisine: count for cuisine, count in results}

    def _get_type_distribution(self) -> dict[str, int]:
        """Get distribution of meal types in historical plans."""
        results = self.session.execute(
            select(Meal.meal_type, func.count(PlanMeal.id))
            .join(PlanMeal, PlanMeal.meal_id == Meal.id)
            .group_by(Meal.meal_type)
            .order_by(func.count(PlanMeal.id).desc())
        ).all()
        return {meal_type: count for meal_type, count in results}

    def get_meal_frequency(self, limit: int = 20) -> list[MealStats]:
        """Get most frequently used meals."""
        stats = self._calculate_meal_stats(date.today())
        return sorted(stats, key=lambda m: m.total_count, reverse=True)[:limit]

    def get_recent_meals(self, weeks: int = 4) -> list[MealStats]:
        """Get meals used in the last N weeks."""
        today = date.today()
        stats = self._calculate_meal_stats(today)
        return [
            m for m in stats
            if m.weeks_since_last_use is not None and m.weeks_since_last_use <= weeks
        ]

    def get_underused_meals(self, min_gap_weeks: int = 4) -> list[MealStats]:
        """Get meals that haven't been used recently."""
        today = date.today()
        stats = self._calculate_meal_stats(today)
        return [
            m for m in stats
            if m.weeks_since_last_use is None or m.weeks_since_last_use >= min_gap_weeks
        ]

    def get_candidates_for_type(
        self,
        meal_type: str,
        exclude_recent_weeks: int = 2,
    ) -> list[MealStats]:
        """Get candidate meals of a specific type, excluding recently used."""
        today = date.today()
        stats = self._calculate_meal_stats(today)

        candidates = [
            m for m in stats
            if m.meal_type == meal_type
            and (m.weeks_since_last_use is None or m.weeks_since_last_use >= exclude_recent_weeks)
        ]

        # Sort by frequency (prefer familiar meals) but with some recency penalty
        return sorted(
            candidates,
            key=lambda m: m.frequency_score - (m.recency_score * 0.5),
            reverse=True,
        )
