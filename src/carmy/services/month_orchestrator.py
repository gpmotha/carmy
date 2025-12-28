"""Month orchestration service for v2 planning.

This service handles:
- Generating week skeletons for a month
- Assigning cooking events based on rhythm
- Selecting meals based on settings and constraints
- Cascade planning (meals that serve multiple days)
"""

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from carmy.models.cooking_event import CookingEvent
from carmy.models.cooking_rhythm import CookingRhythm
from carmy.models.meal import Meal
from carmy.models.meal_slot import MealSlot
from carmy.models.month_plan import MonthPlan, get_season_for_month
from carmy.models.week_skeleton import WeekSkeleton
from carmy.services.analyzer import HistoricalAnalyzer
from carmy.services.seasonality import SeasonalityService
from carmy.services.theme_settings import MonthSettingsV2, THEMES, get_theme


# Use enhanced MonthSettingsV2 as MonthSettings
MonthSettings = MonthSettingsV2


@dataclass
class SpecialDateInfo:
    """Information about a special date for generation."""

    date: date
    event_type: str  # birthday, holiday, guests, etc.
    name: str
    affects_cooking: bool = True


@dataclass
class CookingSlot:
    """A planned cooking slot for a day."""

    date: date
    day_of_week: int
    event_type: str  # big_cook, mid_week, quick, fun_food, special
    effort_level: str  # big, medium, quick
    serves_days: int = 1  # How many days this meal feeds
    meal: Meal | None = None
    is_soup: bool = False
    special_date: SpecialDateInfo | None = None  # If this is a special occasion


@dataclass
class GeneratedWeek:
    """A generated week skeleton with cooking slots."""

    year: int
    week_number: int
    start_date: date
    end_date: date
    cooking_slots: list[CookingSlot] = field(default_factory=list)
    soup_slots: list[CookingSlot] = field(default_factory=list)


@dataclass
class GeneratedMonth:
    """A generated month plan with all weeks."""

    year: int
    month: int
    season: str
    theme: str | None
    weeks: list[GeneratedWeek] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class MonthOrchestrator:
    """Orchestrates monthly meal planning."""

    def __init__(self, session: Session):
        self.session = session
        self.analyzer = HistoricalAnalyzer(session)
        self.seasonality = SeasonalityService()

    def generate_month(
        self,
        year: int,
        month: int,
        settings: MonthSettings | None = None,
        theme: str | None = None,
        special_dates: list[SpecialDateInfo] | None = None,
    ) -> GeneratedMonth:
        """Generate a complete month plan.

        Args:
            year: Year for the plan
            month: Month number (1-12)
            settings: Planning settings (uses defaults if None)
            theme: Optional theme to apply
            special_dates: List of special dates (birthdays, holidays, etc.)

        Returns:
            GeneratedMonth with week skeletons and cooking slots
        """
        if settings is None:
            settings = MonthSettings()
        if special_dates is None:
            special_dates = []

        # Apply theme modifications to settings
        settings = self._apply_theme(settings, theme)

        season = get_season_for_month(month)

        # Get weeks that fall in this month
        weeks_in_month = self._get_weeks_for_month(year, month)

        # Load cooking rhythm
        rhythm = self._load_rhythm()

        # Index special dates by date for quick lookup
        special_dates_map: dict[date, SpecialDateInfo] = {
            sd.date: sd for sd in special_dates if sd.affects_cooking
        }

        # Generate each week
        generated_weeks = []
        used_meals: set[int] = set()  # Track used meals to avoid duplicates

        for week_year, week_num, start_date, end_date in weeks_in_month:
            week = self._generate_week(
                week_year,
                week_num,
                start_date,
                end_date,
                settings,
                rhythm,
                season,
                used_meals,
                special_dates_map,
            )
            generated_weeks.append(week)

            # Track used meals
            for slot in week.cooking_slots + week.soup_slots:
                if slot.meal:
                    used_meals.add(slot.meal.id)

        result = GeneratedMonth(
            year=year,
            month=month,
            season=season,
            theme=theme,
            weeks=generated_weeks,
        )

        # Add any warnings
        result.warnings = self._check_month_warnings(result, settings)

        return result

    def _apply_theme(self, settings: MonthSettings, theme: str | None) -> MonthSettings:
        """Apply theme modifications to settings.

        Uses the enhanced theme system from theme_settings module.
        """
        if not theme:
            return settings

        # Use the new theme system
        return settings.apply_theme(theme)

    def _get_weeks_for_month(
        self, year: int, month: int
    ) -> list[tuple[int, int, date, date]]:
        """Get all ISO weeks that have days in the given month.

        Returns list of (year, week_number, start_date, end_date) tuples.
        """
        # Find first and last day of month
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        weeks = []
        current = first_day

        while current <= last_day:
            iso = current.isocalendar()
            week_year, week_num = iso[0], iso[1]

            # Calculate week start/end
            jan_4 = date(week_year, 1, 4)
            start_of_week_1 = jan_4 - timedelta(days=jan_4.weekday())
            week_start = start_of_week_1 + timedelta(weeks=week_num - 1)
            week_end = week_start + timedelta(days=6)

            # Check if we already added this week
            if not weeks or weeks[-1][1] != week_num or weeks[-1][0] != week_year:
                weeks.append((week_year, week_num, week_start, week_end))

            # Move to next week
            current = week_end + timedelta(days=1)

        return weeks

    def _load_rhythm(self) -> dict[int, CookingRhythm]:
        """Load cooking rhythm patterns by day of week."""
        rhythms = self.session.execute(
            select(CookingRhythm)
        ).scalars().all()

        return {r.day_of_week: r for r in rhythms}

    def _generate_week(
        self,
        year: int,
        week_number: int,
        start_date: date,
        end_date: date,
        settings: MonthSettings,
        rhythm: dict[int, CookingRhythm],
        season: str,
        used_meals: set[int],
        special_dates_map: dict[date, SpecialDateInfo] | None = None,
    ) -> GeneratedWeek:
        """Generate a single week's cooking plan."""
        if special_dates_map is None:
            special_dates_map = {}

        week = GeneratedWeek(
            year=year,
            week_number=week_number,
            start_date=start_date,
            end_date=end_date,
        )

        # Determine cooking days based on rhythm, settings, and special dates
        cooking_days = self._plan_cooking_days(start_date, settings, rhythm, special_dates_map)

        # Get meal candidates
        soup_candidates = self._get_soup_candidates(season, used_meals)
        main_candidates = self._get_main_candidates(season, settings, used_meals)

        # Get special/fancy meal candidates for special dates
        special_candidates = self._get_special_candidates(season, used_meals)

        # Assign soups
        week.soup_slots = self._assign_soups(
            cooking_days,
            soup_candidates,
            settings.soups_per_week,
        )

        # Assign main courses
        week.cooking_slots = self._assign_mains(
            cooking_days,
            main_candidates,
            settings,
            week.soup_slots,  # Check for flavor conflicts with soups
            special_candidates,  # For special dates
        )

        return week

    def _plan_cooking_days(
        self,
        start_date: date,
        settings: MonthSettings,
        rhythm: dict[int, CookingRhythm],
        special_dates_map: dict[date, SpecialDateInfo] | None = None,
    ) -> list[CookingSlot]:
        """Plan which days to cook based on rhythm, settings, and special dates."""
        if special_dates_map is None:
            special_dates_map = {}

        slots = []

        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            day_of_week = current_date.weekday()

            # Check for special date
            special_date = special_dates_map.get(current_date)

            # Check rhythm for this day
            day_rhythm = rhythm.get(day_of_week)

            # Determine if this is a cooking day
            event_type = None
            effort_level = "quick"
            serves_days = 1

            # Special dates always trigger cooking
            if special_date:
                # Special occasion - make it a cooking day
                if special_date.event_type in ("birthday", "holiday", "guests", "party"):
                    event_type = "special"
                    effort_level = "big"  # Put in more effort for special occasions
                    serves_days = 2  # Usually have leftovers from celebrations
                elif special_date.event_type == "away":
                    # Not cooking this day - skip
                    continue
                else:
                    event_type = "special"
                    effort_level = "medium"
                    serves_days = 1
            elif day_of_week in settings.big_cook_days:
                event_type = "big_cook"
                effort_level = "big"
                serves_days = 3 if settings.batch_cooking else 2
            elif day_of_week in settings.mid_week_cook_days:
                event_type = "mid_week"
                effort_level = "medium"
                serves_days = 2
            elif day_of_week in settings.fun_food_days:
                event_type = "fun_food"
                effort_level = "quick"
                serves_days = 1
            elif day_rhythm and day_rhythm.cook_probability > 0.5:
                # Use rhythm data
                event_type = "regular"
                effort_level = day_rhythm.typical_effort or "quick"

            if event_type:
                slots.append(CookingSlot(
                    date=current_date,
                    day_of_week=day_of_week,
                    event_type=event_type,
                    effort_level=effort_level,
                    serves_days=serves_days,
                    special_date=special_date,
                ))

        return slots

    def _get_soup_candidates(
        self,
        season: str,
        used_meals: set[int],
    ) -> list[Meal]:
        """Get candidate soups for the week."""
        query = select(Meal).where(
            Meal.meal_type == "soup",
            Meal.id.notin_(used_meals) if used_meals else True,
        )
        soups = list(self.session.execute(query).scalars().all())

        # Score by seasonality
        scored = []
        for soup in soups:
            score = self.seasonality.score_meal(soup, season).score
            scored.append((soup, score))

        # Sort by score with some randomness
        scored.sort(key=lambda x: x[1] + random.uniform(0, 0.3), reverse=True)
        return [s[0] for s in scored]

    def _get_main_candidates(
        self,
        season: str,
        settings: MonthSettings,
        used_meals: set[int],
    ) -> list[Meal]:
        """Get candidate main courses based on settings.

        Uses enhanced scoring based on:
        - Seasonality
        - Meat/veggie/fish preferences
        - Cuisine balance and preferences
        - Batch cooking suitability
        - Boost keywords from theme
        - Meal type preferences
        """
        # Build base query with meal type filtering
        allowed_types = ["main_course", "pasta", "dinner", "fozelek"]

        # Apply meal type preferences from settings
        if settings.preferred_meal_types:
            allowed_types = [t for t in allowed_types if t in settings.preferred_meal_types] or allowed_types
        if settings.avoided_meal_types:
            allowed_types = [t for t in allowed_types if t not in settings.avoided_meal_types]

        query = select(Meal).where(
            Meal.meal_type.in_(allowed_types),
            Meal.id.notin_(used_meals) if used_meals else True,
        )
        mains = list(self.session.execute(query).scalars().all())

        # Filter and score based on settings
        scored = []
        for meal in mains:
            # Skip avoided cuisines
            if settings.avoided_cuisines and meal.cuisine in settings.avoided_cuisines:
                continue

            score = 1.0

            # Seasonality
            seasonal_score = self.seasonality.score_meal(meal, season).score
            score += seasonal_score * 0.3

            # Meat preference
            if meal.has_meat:
                score += (settings.meat_level - 0.5) * 0.5
            else:
                score += (settings.veggie_level - 0.5) * 0.5

            # Fish preference
            if hasattr(meal, 'has_fish') and meal.has_fish:
                score += (settings.fish_level - 0.3) * 0.6

            # Cuisine balance
            if meal.cuisine == "hungarian":
                score += (1 - settings.cuisine_balance - 0.5) * 0.3
            else:
                score += (settings.cuisine_balance - 0.5) * 0.3

            # Preferred cuisine bonus
            if settings.preferred_cuisines and meal.cuisine in settings.preferred_cuisines:
                score += 0.25

            # Batch cooking preference
            if settings.batch_cooking and meal.good_for_batch:
                score += 0.3

            # Kid friendly bonus
            if meal.kid_friendly:
                score += 0.1

            # Boost keywords matching
            if settings.boost_keywords:
                meal_text = f"{meal.name} {meal.nev} {' '.join(meal.flavor_bases or [])}".lower()
                for keyword in settings.boost_keywords:
                    if keyword.lower() in meal_text:
                        score += 0.15

            scored.append((meal, score))

        # Sort by score with some randomness
        scored.sort(key=lambda x: x[1] + random.uniform(0, 0.3), reverse=True)
        return [s[0] for s in scored]

    def _get_special_candidates(
        self,
        season: str,
        used_meals: set[int],
    ) -> list[Meal]:
        """Get fancy/special meal candidates for celebrations.

        These are meals suitable for birthdays, holidays, and guests:
        - Roasts, steaks, and impressive dishes
        - Kid favorites for kids' birthdays
        - Crowd-pleasers for guests
        """
        # Query for impressive main courses
        query = select(Meal).where(
            Meal.meal_type.in_(["main_course", "dinner"]),
            Meal.id.notin_(used_meals) if used_meals else True,
        )
        mains = list(self.session.execute(query).scalars().all())

        # Score for "specialness"
        scored = []
        special_keywords = [
            "roast", "steak", "beef", "lamb", "duck", "turkey",
            "lasagna", "ragu", "special", "feast", "celebration",
            "birthday", "holiday", "stuffed", "wellington", "tenderloin"
        ]

        for meal in mains:
            score = 0.5

            # Seasonality
            seasonal_score = self.seasonality.score_meal(meal, season).score
            score += seasonal_score * 0.2

            # Check for special keywords in name
            meal_text = f"{meal.name} {meal.nev or ''}".lower()
            for keyword in special_keywords:
                if keyword in meal_text:
                    score += 0.3
                    break

            # Prefer meals that reheat well (for parties with leftovers)
            if meal.reheats_well:
                score += 0.15

            # Kid-friendly bonus (for kids' birthdays)
            if meal.kid_friendly:
                score += 0.1

            # Higher effort is OK for special occasions
            if meal.effort_level in ("big", "medium"):
                score += 0.1

            scored.append((meal, score))

        # Sort by score
        scored.sort(key=lambda x: x[1] + random.uniform(0, 0.2), reverse=True)
        return [s[0] for s in scored]

    def _assign_soups(
        self,
        cooking_days: list[CookingSlot],
        candidates: list[Meal],
        count: int,
    ) -> list[CookingSlot]:
        """Assign soups to cooking days."""
        soup_slots = []
        used_flavors: set[str] = set()

        # Find suitable days for soups (typically big cook or mid-week)
        soup_days = [
            d for d in cooking_days
            if d.event_type in ("big_cook", "mid_week")
        ][:count]

        # If not enough suitable days, use any cooking day
        if len(soup_days) < count:
            soup_days = cooking_days[:count]

        for i, day in enumerate(soup_days):
            if i >= len(candidates):
                break

            # Find a soup without flavor conflicts
            for soup in candidates:
                soup_flavors = {f.lower() for f in soup.flavor_bases}
                if not (soup_flavors & used_flavors):
                    slot = CookingSlot(
                        date=day.date,
                        day_of_week=day.day_of_week,
                        event_type=day.event_type,
                        effort_level="quick",  # Soups are usually quick
                        serves_days=2,  # Soups typically serve 2 days
                        meal=soup,
                        is_soup=True,
                    )
                    soup_slots.append(slot)
                    used_flavors.update(soup_flavors)
                    candidates.remove(soup)
                    break

        return soup_slots

    def _assign_mains(
        self,
        cooking_days: list[CookingSlot],
        candidates: list[Meal],
        settings: MonthSettings,
        soup_slots: list[CookingSlot],
        special_candidates: list[Meal] | None = None,
    ) -> list[CookingSlot]:
        """Assign main courses to cooking days.

        For special dates (birthdays, holidays), uses special_candidates
        to pick more impressive/celebratory meals.
        """
        if special_candidates is None:
            special_candidates = []

        main_slots = []
        used_flavors: set[str] = set()
        meat_count = 0

        # Collect flavors from soups
        for slot in soup_slots:
            if slot.meal:
                used_flavors.update(f.lower() for f in slot.meal.flavor_bases)

        # Assign to each cooking day
        for day in cooking_days:
            if len(main_slots) >= settings.main_courses_per_week:
                break

            # Determine serves_days based on event type
            serves_days = day.serves_days

            # Choose candidate pool based on whether this is a special day
            if day.special_date and day.event_type == "special":
                # Use special candidates for celebrations
                candidate_pool = special_candidates if special_candidates else candidates
            else:
                candidate_pool = candidates

            # Find a suitable meal
            for meal in candidate_pool:
                # Check flavor conflicts
                meal_flavors = {f.lower() for f in meal.flavor_bases}
                if meal_flavors & used_flavors:
                    continue

                # Check meat limit (relaxed for special occasions)
                if meal.has_meat and meat_count >= settings.max_meat_per_week:
                    if not day.special_date:  # Allow meat for special dates
                        continue

                # Lent mode: no meat on Fridays (unless it's a special date)
                if settings.lent_mode and day.day_of_week == 4 and meal.has_meat:
                    if not day.special_date:
                        continue

                # Match effort level to day type
                if day.event_type == "big_cook" and meal.effort_level in ("none", "quick"):
                    # Big cook day should have substantial meal
                    if meal.good_for_batch or meal.reheats_well:
                        pass  # OK if it's good for batch
                    else:
                        continue

                # Assign the meal
                slot = CookingSlot(
                    date=day.date,
                    day_of_week=day.day_of_week,
                    event_type=day.event_type,
                    effort_level=meal.effort_level,
                    serves_days=serves_days,
                    meal=meal,
                    is_soup=False,
                    special_date=day.special_date,
                )
                main_slots.append(slot)
                used_flavors.update(meal_flavors)
                if meal.has_meat:
                    meat_count += 1

                # Remove from both pools if present
                if meal in candidates:
                    candidates.remove(meal)
                if meal in special_candidates:
                    special_candidates.remove(meal)
                break

        return main_slots

    def _check_month_warnings(
        self,
        month: GeneratedMonth,
        settings: MonthSettings,
    ) -> list[str]:
        """Check for warnings in the generated month."""
        warnings = []

        # Check if we have enough variety
        all_meals = []
        for week in month.weeks:
            for slot in week.cooking_slots + week.soup_slots:
                if slot.meal:
                    all_meals.append(slot.meal)

        if len(all_meals) < len(month.weeks) * 4:
            warnings.append(
                f"Low meal variety: only {len(all_meals)} meals for {len(month.weeks)} weeks"
            )

        # Check for any empty weeks
        for week in month.weeks:
            if not week.cooking_slots and not week.soup_slots:
                warnings.append(f"Week {week.week_number} has no cooking events")

        return warnings

    def save_month(self, generated: GeneratedMonth, month_plan: MonthPlan) -> None:
        """Save a generated month to the database.

        Args:
            generated: The generated month plan
            month_plan: The MonthPlan to save to
        """
        for week in generated.weeks:
            # Create or get week skeleton
            skeleton = self.session.execute(
                select(WeekSkeleton).where(
                    WeekSkeleton.year == week.year,
                    WeekSkeleton.week_number == week.week_number,
                )
            ).scalar_one_or_none()

            if skeleton:
                # Clear existing events
                for event in skeleton.cooking_events:
                    self.session.delete(event)
                skeleton.month_plan_id = month_plan.id
            else:
                skeleton = WeekSkeleton(
                    year=week.year,
                    week_number=week.week_number,
                    start_date=week.start_date,
                    end_date=week.end_date,
                    month_plan_id=month_plan.id,
                    status="skeleton",
                )
                self.session.add(skeleton)
                self.session.flush()

            # Add cooking events
            for slot in week.cooking_slots + week.soup_slots:
                if slot.meal:
                    event = CookingEvent(
                        week_skeleton_id=skeleton.id,
                        meal_id=slot.meal.id,
                        cook_date=slot.date,
                        serves_days=slot.serves_days,
                        effort_level=slot.effort_level,
                        event_type=slot.event_type,
                    )
                    self.session.add(event)

        self.session.commit()

    def materialize_week(self, skeleton: WeekSkeleton) -> list[MealSlot]:
        """Materialize a week skeleton into daily meal slots.

        Takes cooking events and generates meal slots including leftovers.
        """
        slots = []

        # Clear existing slots
        for slot in skeleton.meal_slots:
            self.session.delete(slot)

        # Process each cooking event
        for event in skeleton.cooking_events:
            # Create slot for cooking day (fresh)
            slot = MealSlot(
                week_skeleton_id=skeleton.id,
                date=event.cook_date,
                meal_time="dinner",
                meal_id=event.meal_id,
                source="fresh",
                cooking_event_id=event.id,
                status="planned",
            )
            self.session.add(slot)
            slots.append(slot)

            # Create leftover slots for subsequent days
            if event.serves_days > 1:
                for day_offset in range(1, event.serves_days):
                    leftover_date = event.cook_date + timedelta(days=day_offset)

                    # Only within the week
                    if leftover_date <= skeleton.end_date:
                        leftover_slot = MealSlot(
                            week_skeleton_id=skeleton.id,
                            date=leftover_date,
                            meal_time="dinner",
                            meal_id=event.meal_id,
                            source="leftover",
                            cooking_event_id=event.id,
                            leftover_day=day_offset + 1,
                            status="planned",
                        )
                        self.session.add(leftover_slot)
                        slots.append(leftover_slot)

        skeleton.status = "planned"
        self.session.commit()

        return slots
