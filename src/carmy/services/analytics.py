"""Analytics service for meal planning insights."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from carmy.models.meal import Meal
from carmy.models.plan import PlanMeal, WeeklyPlan


@dataclass
class FrequencyReport:
    """Report on meal usage frequency."""

    total_meals: int
    total_uses: int
    most_used: list[tuple[str, int]]  # (name, count)
    least_used: list[tuple[str, int]]
    never_used: list[str]
    average_uses_per_meal: float


@dataclass
class CuisineReport:
    """Report on cuisine distribution."""

    total_meals_with_cuisine: int
    distribution: dict[str, int]  # cuisine -> count
    percentages: dict[str, float]  # cuisine -> percentage
    top_cuisines: list[tuple[str, int, float]]  # (cuisine, count, %)


@dataclass
class TypeReport:
    """Report on meal type distribution."""

    distribution: dict[str, int]
    percentages: dict[str, float]


@dataclass
class LeftoverReport:
    """Report on leftover patterns."""

    total_leftovers: int
    total_meals: int
    leftover_percentage: float
    most_common_leftovers: list[tuple[str, int]]  # (meal_name, times_as_leftover)


@dataclass
class PatternReport:
    """Report on eating patterns."""

    meals_per_week_avg: float
    soups_per_week_avg: float
    mains_per_week_avg: float
    meat_per_week_avg: float
    vegetarian_per_week_avg: float
    weekly_trends: list[dict]  # Per-week stats


@dataclass
class NutritionReport:
    """Report on nutrition trends (if calorie data available)."""

    meals_with_calories: int
    average_calories: float | None
    weekly_averages: list[tuple[int, int, float | None]]  # (year, week, avg_cal)


@dataclass
class AnalyticsReport:
    """Complete analytics report."""

    generated_date: date
    frequency: FrequencyReport
    cuisine: CuisineReport
    meal_types: TypeReport
    leftovers: LeftoverReport
    patterns: PatternReport
    nutrition: NutritionReport


class AnalyticsService:
    """Service for generating analytics and reports."""

    def __init__(self, session: Session):
        self.session = session

    def generate_full_report(self) -> AnalyticsReport:
        """Generate a complete analytics report."""
        return AnalyticsReport(
            generated_date=date.today(),
            frequency=self.get_frequency_report(),
            cuisine=self.get_cuisine_report(),
            meal_types=self.get_type_report(),
            leftovers=self.get_leftover_report(),
            patterns=self.get_pattern_report(),
            nutrition=self.get_nutrition_report(),
        )

    def get_frequency_report(self, limit: int = 10) -> FrequencyReport:
        """Generate meal frequency report."""
        # Get all meals
        meals = self.session.execute(select(Meal)).scalars().all()
        total_meals = len(meals)

        # Get usage counts
        usage_query = (
            select(Meal.name, func.count(PlanMeal.id).label("count"))
            .join(PlanMeal, PlanMeal.meal_id == Meal.id)
            .group_by(Meal.id, Meal.name)
            .order_by(func.count(PlanMeal.id).desc())
        )
        usage_results = self.session.execute(usage_query).all()

        used_meals = {name for name, _ in usage_results}
        total_uses = sum(count for _, count in usage_results)

        # Most used
        most_used = [(name, count) for name, count in usage_results[:limit]]

        # Least used (excluding never used)
        least_used = [(name, count) for name, count in reversed(usage_results[-limit:])]

        # Never used
        never_used = [m.name for m in meals if m.name not in used_meals]

        avg_uses = total_uses / total_meals if total_meals > 0 else 0

        return FrequencyReport(
            total_meals=total_meals,
            total_uses=total_uses,
            most_used=most_used,
            least_used=least_used,
            never_used=never_used,
            average_uses_per_meal=avg_uses,
        )

    def get_cuisine_report(self) -> CuisineReport:
        """Generate cuisine distribution report."""
        # Count meals per cuisine in plans
        query = (
            select(Meal.cuisine, func.count(PlanMeal.id).label("count"))
            .join(PlanMeal, PlanMeal.meal_id == Meal.id)
            .where(Meal.cuisine.isnot(None))
            .group_by(Meal.cuisine)
            .order_by(func.count(PlanMeal.id).desc())
        )
        results = self.session.execute(query).all()

        distribution = {cuisine: count for cuisine, count in results}
        total = sum(distribution.values())

        percentages = {
            cuisine: (count / total * 100) if total > 0 else 0
            for cuisine, count in distribution.items()
        }

        top_cuisines = [
            (cuisine, count, percentages[cuisine])
            for cuisine, count in results[:10]
        ]

        return CuisineReport(
            total_meals_with_cuisine=total,
            distribution=distribution,
            percentages=percentages,
            top_cuisines=top_cuisines,
        )

    def get_type_report(self) -> TypeReport:
        """Generate meal type distribution report."""
        query = (
            select(Meal.meal_type, func.count(PlanMeal.id).label("count"))
            .join(PlanMeal, PlanMeal.meal_id == Meal.id)
            .group_by(Meal.meal_type)
            .order_by(func.count(PlanMeal.id).desc())
        )
        results = self.session.execute(query).all()

        distribution = {meal_type: count for meal_type, count in results}
        total = sum(distribution.values())

        percentages = {
            meal_type: (count / total * 100) if total > 0 else 0
            for meal_type, count in distribution.items()
        }

        return TypeReport(distribution=distribution, percentages=percentages)

    def get_leftover_report(self, limit: int = 10) -> LeftoverReport:
        """Generate leftover tracking report."""
        # Total plan meals
        total_meals = self.session.execute(
            select(func.count(PlanMeal.id)).where(PlanMeal.meal_id.isnot(None))
        ).scalar() or 0

        # Total leftovers
        total_leftovers = self.session.execute(
            select(func.count(PlanMeal.id)).where(
                PlanMeal.is_leftover == True,
                PlanMeal.meal_id.isnot(None),
            )
        ).scalar() or 0

        # Most common leftovers
        leftover_query = (
            select(Meal.name, func.count(PlanMeal.id).label("count"))
            .join(PlanMeal, PlanMeal.meal_id == Meal.id)
            .where(PlanMeal.is_leftover == True)
            .group_by(Meal.id, Meal.name)
            .order_by(func.count(PlanMeal.id).desc())
            .limit(limit)
        )
        leftover_results = self.session.execute(leftover_query).all()

        leftover_pct = (total_leftovers / total_meals * 100) if total_meals > 0 else 0

        return LeftoverReport(
            total_leftovers=total_leftovers,
            total_meals=total_meals,
            leftover_percentage=leftover_pct,
            most_common_leftovers=[(name, count) for name, count in leftover_results],
        )

    def get_pattern_report(self) -> PatternReport:
        """Generate eating pattern report."""
        # Get all plans with their meals
        plans = self.session.execute(
            select(WeeklyPlan).order_by(WeeklyPlan.year, WeeklyPlan.week_number)
        ).scalars().all()

        if not plans:
            return PatternReport(
                meals_per_week_avg=0,
                soups_per_week_avg=0,
                mains_per_week_avg=0,
                meat_per_week_avg=0,
                vegetarian_per_week_avg=0,
                weekly_trends=[],
            )

        weekly_trends = []
        total_meals = 0
        total_soups = 0
        total_mains = 0
        total_meat = 0
        total_veg = 0

        for plan in plans:
            meals = [pm.meal for pm in plan.plan_meals if pm.meal and not pm.is_leftover]
            soups = [m for m in meals if m.meal_type == "soup"]
            mains = [m for m in meals if m.meal_type in ("main_course", "pasta", "dinner")]
            meat = [m for m in meals if m.has_meat]
            veg = [m for m in meals if m.is_vegetarian]

            week_data = {
                "year": plan.year,
                "week": plan.week_number,
                "total": len(meals),
                "soups": len(soups),
                "mains": len(mains),
                "meat": len(meat),
                "vegetarian": len(veg),
            }
            weekly_trends.append(week_data)

            total_meals += len(meals)
            total_soups += len(soups)
            total_mains += len(mains)
            total_meat += len(meat)
            total_veg += len(veg)

        num_weeks = len(plans)

        return PatternReport(
            meals_per_week_avg=total_meals / num_weeks if num_weeks > 0 else 0,
            soups_per_week_avg=total_soups / num_weeks if num_weeks > 0 else 0,
            mains_per_week_avg=total_mains / num_weeks if num_weeks > 0 else 0,
            meat_per_week_avg=total_meat / num_weeks if num_weeks > 0 else 0,
            vegetarian_per_week_avg=total_veg / num_weeks if num_weeks > 0 else 0,
            weekly_trends=weekly_trends,
        )

    def get_nutrition_report(self) -> NutritionReport:
        """Generate nutrition trends report."""
        # Get meals with calories
        meals_with_cal = self.session.execute(
            select(func.count(Meal.id)).where(Meal.calories.isnot(None))
        ).scalar() or 0

        # Average calories
        avg_cal = self.session.execute(
            select(func.avg(Meal.calories)).where(Meal.calories.isnot(None))
        ).scalar()

        # Weekly averages
        weekly_query = (
            select(
                WeeklyPlan.year,
                WeeklyPlan.week_number,
                func.avg(Meal.calories).label("avg_cal"),
            )
            .join(PlanMeal, PlanMeal.plan_id == WeeklyPlan.id)
            .join(Meal, PlanMeal.meal_id == Meal.id)
            .where(Meal.calories.isnot(None))
            .group_by(WeeklyPlan.year, WeeklyPlan.week_number)
            .order_by(WeeklyPlan.year, WeeklyPlan.week_number)
        )
        weekly_results = self.session.execute(weekly_query).all()

        return NutritionReport(
            meals_with_calories=meals_with_cal,
            average_calories=float(avg_cal) if avg_cal else None,
            weekly_averages=[(y, w, float(c) if c else None) for y, w, c in weekly_results],
        )

    def get_meal_history(self, meal_id: int) -> list[dict]:
        """Get usage history for a specific meal."""
        query = (
            select(WeeklyPlan.year, WeeklyPlan.week_number, WeeklyPlan.start_date, PlanMeal.is_leftover)
            .join(PlanMeal, PlanMeal.plan_id == WeeklyPlan.id)
            .where(PlanMeal.meal_id == meal_id)
            .order_by(WeeklyPlan.year.desc(), WeeklyPlan.week_number.desc())
        )
        results = self.session.execute(query).all()

        return [
            {
                "year": year,
                "week": week,
                "date": start_date,
                "is_leftover": is_leftover,
            }
            for year, week, start_date, is_leftover in results
        ]

    def get_trends(self, weeks: int = 12) -> dict:
        """Get trends over recent weeks."""
        query = (
            select(WeeklyPlan)
            .order_by(WeeklyPlan.year.desc(), WeeklyPlan.week_number.desc())
            .limit(weeks)
        )
        plans = list(reversed(self.session.execute(query).scalars().all()))

        trends = {
            "weeks": [],
            "meal_counts": [],
            "meat_counts": [],
            "soup_counts": [],
        }

        for plan in plans:
            meals = [pm.meal for pm in plan.plan_meals if pm.meal and not pm.is_leftover]
            trends["weeks"].append(f"W{plan.week_number}")
            trends["meal_counts"].append(len(meals))
            trends["meat_counts"].append(sum(1 for m in meals if m.has_meat))
            trends["soup_counts"].append(sum(1 for m in meals if m.meal_type == "soup"))

        return trends
