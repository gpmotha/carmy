"""Plan generation service for auto-creating weekly meal plans."""

import random
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from carmy.models.meal import Meal
from carmy.models.plan import PlanMeal, WeeklyPlan
from carmy.services.analyzer import HistoricalAnalyzer, MealStats
from carmy.services.rules_engine import RulesEngine, ValidationResult
from carmy.services.seasonality import SeasonalityService, get_current_season


@dataclass
class GeneratedPlan:
    """A generated weekly plan suggestion."""

    year: int
    week_number: int
    start_date: date
    soups: list[Meal]
    main_courses: list[Meal]
    validation: ValidationResult | None = None
    notes: str = ""
    season: str = ""


@dataclass
class GeneratorConfig:
    """Configuration for the plan generator."""

    soups_count: int = 2
    main_courses_count: int = 4
    max_meat_dishes: int = 3
    exclude_recent_weeks: int = 2
    prefer_frequency: bool = True  # Prefer frequently used meals
    randomness: float = 0.3  # 0 = deterministic, 1 = fully random
    use_seasonality: bool = True  # Prefer seasonal meals
    seasonality_weight: float = 0.3  # How much to weight seasonality (0-1)


class PlanGenerator:
    """Generates weekly meal plans based on history and rules."""

    def __init__(
        self,
        session: Session,
        config: GeneratorConfig | None = None,
    ):
        self.session = session
        self.config = config or GeneratorConfig()
        self.analyzer = HistoricalAnalyzer(session)
        self.rules = RulesEngine(
            soups_per_week=self.config.soups_count,
            main_courses_per_week=self.config.main_courses_count,
            max_meat_dishes=self.config.max_meat_dishes,
        )
        self.seasonality = SeasonalityService()

    def generate(
        self,
        year: int,
        week_number: int,
        start_date: date,
        season: str | None = None,
    ) -> GeneratedPlan:
        """Generate a weekly plan suggestion.

        Args:
            year: The year for the plan
            week_number: The ISO week number
            start_date: The Monday of the week
            season: Override season (defaults to season of start_date)

        Returns:
            GeneratedPlan with suggested meals
        """
        # Determine season
        if season is None:
            season = get_current_season(start_date)

        # Get candidates for each type
        soup_candidates = self._get_soup_candidates(season)
        main_candidates = self._get_main_candidates(season)

        # Select soups
        selected_soups = self._select_meals(
            soup_candidates,
            count=self.config.soups_count,
            check_flavor_conflicts=True,
            season=season,
        )

        # Select main courses (checking for flavor conflicts with soups)
        selected_mains = self._select_meals(
            main_candidates,
            count=self.config.main_courses_count,
            existing_meals=selected_soups,
            check_flavor_conflicts=True,
            max_meat=self.config.max_meat_dishes,
            season=season,
        )

        plan = GeneratedPlan(
            year=year,
            week_number=week_number,
            start_date=start_date,
            soups=selected_soups,
            main_courses=selected_mains,
            season=season,
        )

        # Validate the generated plan
        plan.validation = self._validate_plan(plan)

        return plan

    def _get_soup_candidates(self, season: str | None = None) -> list[MealStats]:
        """Get candidate soups, excluding recently used."""
        candidates = self.analyzer.get_candidates_for_type(
            "soup",
            exclude_recent_weeks=self.config.exclude_recent_weeks,
        )

        # Apply seasonality scoring if enabled
        if self.config.use_seasonality and season:
            candidates = self._apply_seasonality_boost(candidates, season)

        return candidates

    def _get_main_candidates(self, season: str | None = None) -> list[MealStats]:
        """Get candidate main courses, excluding recently used."""
        # Include main_course, pasta, dinner types
        candidates = []
        for meal_type in ["main_course", "pasta", "dinner"]:
            candidates.extend(
                self.analyzer.get_candidates_for_type(
                    meal_type,
                    exclude_recent_weeks=self.config.exclude_recent_weeks,
                )
            )

        # Apply seasonality scoring if enabled
        if self.config.use_seasonality and season:
            candidates = self._apply_seasonality_boost(candidates, season)

        return candidates

    def _apply_seasonality_boost(
        self,
        candidates: list[MealStats],
        season: str,
    ) -> list[MealStats]:
        """Reorder candidates to prefer seasonal meals.

        Args:
            candidates: List of meal candidates
            season: Current season

        Returns:
            Reordered candidates with seasonal meals boosted
        """
        if not candidates:
            return candidates

        # Score each candidate for seasonality
        scored = []
        for stat in candidates:
            meal = self.session.get(Meal, stat.meal_id)
            if meal:
                seasonal_score = self.seasonality.score_meal(meal, season)
                # Combine frequency and seasonality
                combined_score = (
                    stat.frequency_score * (1 - self.config.seasonality_weight)
                    + seasonal_score.score * 10 * self.config.seasonality_weight
                )
                scored.append((stat, combined_score))
            else:
                scored.append((stat, stat.frequency_score))

        # Sort by combined score
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored]

    def _select_meals(
        self,
        candidates: list[MealStats],
        count: int,
        existing_meals: list[Meal] | None = None,
        check_flavor_conflicts: bool = True,
        max_meat: int | None = None,
        season: str | None = None,
    ) -> list[Meal]:
        """Select meals from candidates.

        Args:
            candidates: List of candidate meal stats
            count: Number of meals to select
            existing_meals: Already selected meals to check conflicts against
            check_flavor_conflicts: Whether to check for flavor base conflicts
            max_meat: Maximum meat dishes allowed (across existing + new)
            season: Current season for scoring (unused in selection, used in sorting)
        """
        if not candidates:
            return []

        selected: list[Meal] = []
        used_flavors: set[str] = set()
        meat_count = 0

        # Collect existing flavors and meat count
        if existing_meals:
            for meal in existing_meals:
                used_flavors.update(f.lower() for f in meal.flavor_bases)
                if meal.has_meat:
                    meat_count += 1

        # Apply randomness to candidate order
        if self.config.randomness > 0:
            candidates = self._shuffle_with_preference(candidates)

        for stat in candidates:
            if len(selected) >= count:
                break

            # Load the actual meal
            meal = self.session.get(Meal, stat.meal_id)
            if not meal:
                continue

            # Check meat limit
            if max_meat is not None and meal.has_meat:
                if meat_count >= max_meat:
                    continue

            # Check flavor conflicts
            if check_flavor_conflicts:
                meal_flavors = {f.lower() for f in meal.flavor_bases}
                if meal_flavors & used_flavors:
                    continue  # Skip - flavor conflict

            # Add the meal
            selected.append(meal)
            used_flavors.update(f.lower() for f in meal.flavor_bases)
            if meal.has_meat:
                meat_count += 1

        return selected

    def _shuffle_with_preference(self, candidates: list[MealStats]) -> list[MealStats]:
        """Shuffle candidates while maintaining some preference ordering."""
        if not candidates:
            return candidates

        # Split into chunks and shuffle within chunks
        result = []
        chunk_size = max(1, int(len(candidates) * self.config.randomness))

        for i in range(0, len(candidates), chunk_size):
            chunk = candidates[i : i + chunk_size]
            random.shuffle(chunk)
            result.extend(chunk)

        return result

    def _validate_plan(self, plan: GeneratedPlan) -> ValidationResult:
        """Validate the generated plan against rules."""
        # Create a temporary WeeklyPlan object for validation
        temp_plan = WeeklyPlan(
            year=plan.year,
            week_number=plan.week_number,
            start_date=plan.start_date,
        )

        # Add meals as PlanMeal objects
        for meal in plan.soups + plan.main_courses:
            pm = PlanMeal(meal=meal, is_leftover=False)
            temp_plan.plan_meals.append(pm)

        return self.rules.validate(temp_plan)

    def regenerate_slot(
        self,
        plan: GeneratedPlan,
        slot_type: str,  # "soup" or "main"
        index: int,
    ) -> GeneratedPlan:
        """Regenerate a single slot in the plan.

        Args:
            plan: The existing generated plan
            slot_type: "soup" or "main"
            index: Which slot to regenerate (0-indexed)

        Returns:
            Updated plan with new meal in the specified slot
        """
        if slot_type == "soup":
            if index >= len(plan.soups):
                return plan

            # Get candidates excluding other selected meals
            other_meals = [m for i, m in enumerate(plan.soups) if i != index]
            other_meals.extend(plan.main_courses)

            candidates = self._get_soup_candidates()
            new_meals = self._select_meals(
                candidates,
                count=1,
                existing_meals=other_meals,
                check_flavor_conflicts=True,
            )

            if new_meals:
                plan.soups[index] = new_meals[0]

        elif slot_type == "main":
            if index >= len(plan.main_courses):
                return plan

            other_meals = plan.soups.copy()
            other_meals.extend(m for i, m in enumerate(plan.main_courses) if i != index)

            # Calculate current meat count excluding the slot
            current_meat = sum(1 for m in other_meals if m.has_meat)
            remaining_meat = self.config.max_meat_dishes - current_meat

            candidates = self._get_main_candidates()
            new_meals = self._select_meals(
                candidates,
                count=1,
                existing_meals=other_meals,
                check_flavor_conflicts=True,
                max_meat=self.config.max_meat_dishes,
            )

            if new_meals:
                plan.main_courses[index] = new_meals[0]

        # Re-validate
        plan.validation = self._validate_plan(plan)
        return plan

    def save_plan(self, plan: GeneratedPlan) -> WeeklyPlan:
        """Save a generated plan to the database.

        Args:
            plan: The generated plan to save

        Returns:
            The created WeeklyPlan
        """
        # Check if plan already exists
        existing = self.session.execute(
            select(WeeklyPlan).where(
                WeeklyPlan.year == plan.year,
                WeeklyPlan.week_number == plan.week_number,
            )
        ).scalar_one_or_none()

        if existing:
            raise ValueError(
                f"Plan for week {plan.week_number}, {plan.year} already exists"
            )

        weekly_plan = WeeklyPlan(
            year=plan.year,
            week_number=plan.week_number,
            start_date=plan.start_date,
            notes=plan.notes,
        )
        self.session.add(weekly_plan)
        self.session.flush()

        # Add soups and main courses
        for meal in plan.soups + plan.main_courses:
            pm = PlanMeal(
                plan_id=weekly_plan.id,
                meal_id=meal.id,
                is_leftover=False,
            )
            self.session.add(pm)

        self.session.commit()
        return weekly_plan
