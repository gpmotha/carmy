"""Week materialization service for v2 planning.

This service transforms week skeletons with cooking events into
fully populated daily meal slots, including:
- Fresh cooking day meals
- Leftover chains across multiple days
- Soup slots (parallel track)
- Light meal gap filling
- Lunch assignments
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from carmy.models.cooking_event import CookingEvent
from carmy.models.meal import Meal
from carmy.models.meal_slot import MealSlot, MealSource, MealTime, SlotStatus
from carmy.models.week_skeleton import WeekSkeleton


@dataclass
class DayPlan:
    """Plan for a single day's meals."""

    date: date
    day_of_week: int  # 0=Monday, 6=Sunday

    # Dinner slot
    dinner_meal_id: Optional[int] = None
    dinner_source: str = "light"
    dinner_cooking_event_id: Optional[int] = None
    dinner_leftover_day: Optional[int] = None

    # Lunch slot
    lunch_meal_id: Optional[int] = None
    lunch_source: str = "light"
    lunch_cooking_event_id: Optional[int] = None
    lunch_leftover_day: Optional[int] = None

    # Soup slot (can be eaten at lunch or dinner alongside main)
    soup_meal_id: Optional[int] = None
    soup_source: str = "fresh"
    soup_cooking_event_id: Optional[int] = None
    soup_leftover_day: Optional[int] = None

    # Special flags
    is_eating_out: bool = False
    notes: str = ""


@dataclass
class MaterializedWeek:
    """Result of materializing a week skeleton."""

    skeleton_id: int
    year: int
    week_number: int
    start_date: date
    end_date: date
    days: list[DayPlan] = field(default_factory=list)
    slots_created: int = 0
    warnings: list[str] = field(default_factory=list)


class WeekMaterializer:
    """Materializes week skeletons into daily meal slots."""

    def __init__(self, session: Session):
        self.session = session

    def materialize(
        self,
        skeleton: WeekSkeleton,
        include_lunch: bool = True,
        include_soup: bool = True,
    ) -> MaterializedWeek:
        """Materialize a week skeleton into daily meal slots.

        Args:
            skeleton: The week skeleton to materialize
            include_lunch: Whether to generate lunch slots
            include_soup: Whether to generate soup slots

        Returns:
            MaterializedWeek with all generated data
        """
        result = MaterializedWeek(
            skeleton_id=skeleton.id,
            year=skeleton.year,
            week_number=skeleton.week_number,
            start_date=skeleton.start_date,
            end_date=skeleton.end_date,
        )

        # Initialize day plans for each day of the week
        day_plans: dict[date, DayPlan] = {}
        current_date = skeleton.start_date
        while current_date <= skeleton.end_date:
            day_plans[current_date] = DayPlan(
                date=current_date,
                day_of_week=current_date.weekday(),
            )
            current_date += timedelta(days=1)

        # Process cooking events to populate dinner slots
        self._process_cooking_events(skeleton.cooking_events, day_plans, result)

        # Process soup events (parallel track)
        if include_soup:
            self._process_soup_events(skeleton.cooking_events, day_plans, result)

        # Assign leftovers to lunch slots
        if include_lunch:
            self._assign_lunch_leftovers(day_plans, result)

        # Fill gaps with light meals
        self._fill_gaps(day_plans, result)

        # Convert day plans to meal slots
        result.days = list(day_plans.values())

        return result

    def _process_cooking_events(
        self,
        events: list[CookingEvent],
        day_plans: dict[date, DayPlan],
        result: MaterializedWeek,
    ) -> None:
        """Process cooking events to populate dinner slots with fresh meals and leftovers."""
        # Separate main course events from soup events
        main_events = [e for e in events if e.meal and e.meal.meal_type != "soup"]

        for event in main_events:
            cook_date = event.cook_date
            serves_days = event.serves_days or 1

            # Day 1: Fresh cooking day
            if cook_date in day_plans:
                plan = day_plans[cook_date]
                if plan.dinner_meal_id is None:  # Don't overwrite existing
                    plan.dinner_meal_id = event.meal_id
                    plan.dinner_source = MealSource.FRESH.value
                    plan.dinner_cooking_event_id = event.id
                    plan.dinner_leftover_day = 1
                else:
                    result.warnings.append(
                        f"Dinner conflict on {cook_date}: {event.meal.name if event.meal else 'Unknown'}"
                    )

            # Days 2+: Leftovers
            for day_offset in range(1, serves_days):
                leftover_date = cook_date + timedelta(days=day_offset)

                if leftover_date in day_plans:
                    plan = day_plans[leftover_date]
                    if plan.dinner_meal_id is None:  # Don't overwrite
                        plan.dinner_meal_id = event.meal_id
                        plan.dinner_source = MealSource.LEFTOVER.value
                        plan.dinner_cooking_event_id = event.id
                        plan.dinner_leftover_day = day_offset + 1
                    else:
                        # Leftover can go to lunch instead
                        if plan.lunch_meal_id is None:
                            plan.lunch_meal_id = event.meal_id
                            plan.lunch_source = MealSource.LEFTOVER.value
                            plan.lunch_cooking_event_id = event.id
                            plan.lunch_leftover_day = day_offset + 1

    def _process_soup_events(
        self,
        events: list[CookingEvent],
        day_plans: dict[date, DayPlan],
        result: MaterializedWeek,
    ) -> None:
        """Process soup cooking events as a parallel track."""
        soup_events = [e for e in events if e.meal and e.meal.meal_type == "soup"]

        for event in soup_events:
            cook_date = event.cook_date
            serves_days = event.serves_days or 2  # Soups typically serve 2 days

            # Day 1: Fresh soup
            if cook_date in day_plans:
                plan = day_plans[cook_date]
                if plan.soup_meal_id is None:
                    plan.soup_meal_id = event.meal_id
                    plan.soup_source = MealSource.FRESH.value
                    plan.soup_cooking_event_id = event.id
                    plan.soup_leftover_day = 1

            # Days 2+: Leftover soup
            for day_offset in range(1, serves_days):
                leftover_date = cook_date + timedelta(days=day_offset)

                if leftover_date in day_plans:
                    plan = day_plans[leftover_date]
                    if plan.soup_meal_id is None:
                        plan.soup_meal_id = event.meal_id
                        plan.soup_source = MealSource.LEFTOVER.value
                        plan.soup_cooking_event_id = event.id
                        plan.soup_leftover_day = day_offset + 1

    def _assign_lunch_leftovers(
        self,
        day_plans: dict[date, DayPlan],
        result: MaterializedWeek,
    ) -> None:
        """Assign leftovers from previous day's dinner to lunch slots."""
        sorted_dates = sorted(day_plans.keys())

        for i, current_date in enumerate(sorted_dates):
            plan = day_plans[current_date]

            # Skip if lunch already assigned
            if plan.lunch_meal_id is not None:
                continue

            # Check previous day for leftovers
            if i > 0:
                prev_date = sorted_dates[i - 1]
                prev_plan = day_plans[prev_date]

                # If previous dinner was fresh or day-1 leftover, and the meal reheats well
                if (
                    prev_plan.dinner_meal_id
                    and prev_plan.dinner_source in (MealSource.FRESH.value, MealSource.LEFTOVER.value)
                    and prev_plan.dinner_leftover_day
                    and prev_plan.dinner_leftover_day <= 2  # Only recent leftovers
                ):
                    # Get the meal to check if it reheats well
                    meal = self.session.get(Meal, prev_plan.dinner_meal_id)
                    if meal and meal.reheats_well:
                        plan.lunch_meal_id = prev_plan.dinner_meal_id
                        plan.lunch_source = MealSource.LEFTOVER.value
                        plan.lunch_cooking_event_id = prev_plan.dinner_cooking_event_id
                        plan.lunch_leftover_day = (prev_plan.dinner_leftover_day or 1) + 1

    def _fill_gaps(
        self,
        day_plans: dict[date, DayPlan],
        result: MaterializedWeek,
    ) -> None:
        """Fill empty slots with light meal placeholders."""
        for plan in day_plans.values():
            # Fill dinner gaps
            if plan.dinner_meal_id is None and not plan.is_eating_out:
                plan.dinner_source = MealSource.LIGHT.value

            # Fill lunch gaps
            if plan.lunch_meal_id is None:
                plan.lunch_source = MealSource.LIGHT.value

    def save_slots(self, skeleton: WeekSkeleton, materialized: MaterializedWeek) -> list[MealSlot]:
        """Save materialized week to database as MealSlots.

        Args:
            skeleton: The week skeleton
            materialized: The materialized week data

        Returns:
            List of created MealSlot objects
        """
        # Clear existing slots
        for slot in list(skeleton.meal_slots):
            self.session.delete(slot)
        self.session.flush()

        created_slots: list[MealSlot] = []

        for day_plan in materialized.days:
            # Create dinner slot
            if day_plan.dinner_meal_id or day_plan.dinner_source != MealSource.LIGHT.value:
                dinner_slot = MealSlot(
                    week_skeleton_id=skeleton.id,
                    date=day_plan.date,
                    meal_time=MealTime.DINNER.value,
                    meal_id=day_plan.dinner_meal_id,
                    source=day_plan.dinner_source,
                    cooking_event_id=day_plan.dinner_cooking_event_id,
                    leftover_day=day_plan.dinner_leftover_day,
                    status=SlotStatus.PLANNED.value,
                    notes=day_plan.notes if day_plan.notes else None,
                )
                self.session.add(dinner_slot)
                created_slots.append(dinner_slot)

            # Create lunch slot
            if day_plan.lunch_meal_id or day_plan.lunch_source != MealSource.LIGHT.value:
                lunch_slot = MealSlot(
                    week_skeleton_id=skeleton.id,
                    date=day_plan.date,
                    meal_time=MealTime.LUNCH.value,
                    meal_id=day_plan.lunch_meal_id,
                    source=day_plan.lunch_source,
                    cooking_event_id=day_plan.lunch_cooking_event_id,
                    leftover_day=day_plan.lunch_leftover_day,
                    status=SlotStatus.PLANNED.value,
                )
                self.session.add(lunch_slot)
                created_slots.append(lunch_slot)

            # Create soup slot if present
            if day_plan.soup_meal_id:
                soup_slot = MealSlot(
                    week_skeleton_id=skeleton.id,
                    date=day_plan.date,
                    meal_time=MealTime.LUNCH.value,  # Soup often at lunch
                    meal_id=day_plan.soup_meal_id,
                    source=day_plan.soup_source,
                    cooking_event_id=day_plan.soup_cooking_event_id,
                    leftover_day=day_plan.soup_leftover_day,
                    status=SlotStatus.PLANNED.value,
                    notes="Soup",
                )
                self.session.add(soup_slot)
                created_slots.append(soup_slot)

        # Update skeleton status
        skeleton.status = "materialized"
        self.session.commit()

        materialized.slots_created = len(created_slots)
        return created_slots

    def materialize_and_save(
        self,
        skeleton: WeekSkeleton,
        include_lunch: bool = True,
        include_soup: bool = True,
    ) -> tuple[MaterializedWeek, list[MealSlot]]:
        """Materialize a week skeleton and save to database.

        Args:
            skeleton: The week skeleton to materialize
            include_lunch: Whether to generate lunch slots
            include_soup: Whether to generate soup slots

        Returns:
            Tuple of (MaterializedWeek, list of MealSlots)
        """
        materialized = self.materialize(skeleton, include_lunch, include_soup)
        slots = self.save_slots(skeleton, materialized)
        return materialized, slots

    def get_week_summary(self, skeleton: WeekSkeleton) -> dict:
        """Get a summary of the week's meal plan.

        Args:
            skeleton: The week skeleton

        Returns:
            Summary dict with counts and details
        """
        slots = skeleton.meal_slots

        summary = {
            "total_slots": len(slots),
            "dinners": 0,
            "lunches": 0,
            "fresh_meals": 0,
            "leftover_meals": 0,
            "light_meals": 0,
            "eat_out": 0,
            "soups": 0,
            "by_day": {},
        }

        for slot in slots:
            # Count by meal time
            if slot.meal_time == MealTime.DINNER.value:
                summary["dinners"] += 1
            elif slot.meal_time == MealTime.LUNCH.value:
                summary["lunches"] += 1

            # Count by source
            if slot.source == MealSource.FRESH.value:
                summary["fresh_meals"] += 1
            elif slot.source == MealSource.LEFTOVER.value:
                summary["leftover_meals"] += 1
            elif slot.source == MealSource.LIGHT.value:
                summary["light_meals"] += 1
            elif slot.source == MealSource.EAT_OUT.value:
                summary["eat_out"] += 1

            # Count soups
            if slot.notes == "Soup":
                summary["soups"] += 1

            # Group by day
            day_str = slot.date.isoformat()
            if day_str not in summary["by_day"]:
                summary["by_day"][day_str] = {
                    "date": slot.date,
                    "day_name": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][slot.date.weekday()],
                    "slots": [],
                }
            summary["by_day"][day_str]["slots"].append({
                "meal_time": slot.meal_time,
                "meal_id": slot.meal_id,
                "meal_name": slot.meal.name if slot.meal else None,
                "source": slot.source,
                "leftover_day": slot.leftover_day,
            })

        return summary


def materialize_week(session: Session, skeleton: WeekSkeleton) -> MaterializedWeek:
    """Convenience function to materialize a week skeleton.

    Args:
        session: Database session
        skeleton: The week skeleton to materialize

    Returns:
        MaterializedWeek with all generated data
    """
    materializer = WeekMaterializer(session)
    return materializer.materialize(skeleton)


def materialize_and_save_week(
    session: Session,
    skeleton: WeekSkeleton,
) -> tuple[MaterializedWeek, list[MealSlot]]:
    """Convenience function to materialize and save a week skeleton.

    Args:
        session: Database session
        skeleton: The week skeleton to materialize

    Returns:
        Tuple of (MaterializedWeek, list of MealSlots)
    """
    materializer = WeekMaterializer(session)
    return materializer.materialize_and_save(skeleton)
