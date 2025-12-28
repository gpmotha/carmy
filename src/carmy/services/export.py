"""Export services for meal plans."""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Session

from carmy.models.meal import Meal
from carmy.models.plan import WeeklyPlan

if TYPE_CHECKING:
    from carmy.models.week_skeleton import WeekSkeleton
    from carmy.models.month_plan import MonthPlan


@dataclass
class ShoppingItem:
    """An item on the shopping list."""

    name: str
    meal_names: list[str]  # Which meals need this
    category: str = "other"
    quantity: str = ""


@dataclass
class ShoppingList:
    """A shopping list for a weekly plan."""

    week: int
    year: int
    start_date: date
    items: list[ShoppingItem]
    meals: list[str]

    def to_text(self, include_meals: bool = True) -> str:
        """Export as plain text."""
        lines = [
            f"Shopping List - Week {self.week}, {self.year}",
            f"Starting: {self.start_date}",
            "",
        ]

        if include_meals:
            lines.append("Meals this week:")
            for meal in self.meals:
                lines.append(f"  - {meal}")
            lines.append("")

        # Group by category
        by_category: dict[str, list[ShoppingItem]] = {}
        for item in self.items:
            by_category.setdefault(item.category, []).append(item)

        for category, items in sorted(by_category.items()):
            lines.append(f"{category.upper()}:")
            for item in items:
                qty = f" ({item.quantity})" if item.quantity else ""
                lines.append(f"  [ ] {item.name}{qty}")
            lines.append("")

        return "\n".join(lines)

    def to_markdown(self, include_meals: bool = True) -> str:
        """Export as markdown."""
        lines = [
            f"# Shopping List - Week {self.week}, {self.year}",
            f"*Starting: {self.start_date}*",
            "",
        ]

        if include_meals:
            lines.append("## Meals this week")
            for meal in self.meals:
                lines.append(f"- {meal}")
            lines.append("")

        # Group by category
        by_category: dict[str, list[ShoppingItem]] = {}
        for item in self.items:
            by_category.setdefault(item.category, []).append(item)

        lines.append("## Shopping List")
        for category, items in sorted(by_category.items()):
            lines.append(f"\n### {category.title()}")
            for item in items:
                qty = f" ({item.quantity})" if item.quantity else ""
                lines.append(f"- [ ] {item.name}{qty}")

        return "\n".join(lines)


class ExportService:
    """Service for exporting meal plans in various formats."""

    # Common ingredient categories
    CATEGORIES = {
        # Proteins
        "chicken": "protein",
        "beef": "protein",
        "pork": "protein",
        "fish": "protein",
        "salmon": "protein",
        "tuna": "protein",
        "bacon": "protein",
        "ham": "protein",
        "sausage": "protein",
        "egg": "protein",
        "tofu": "protein",
        # Dairy
        "milk": "dairy",
        "cheese": "dairy",
        "butter": "dairy",
        "cream": "dairy",
        "yogurt": "dairy",
        "sour cream": "dairy",
        # Produce
        "tomato": "produce",
        "potato": "produce",
        "onion": "produce",
        "garlic": "produce",
        "carrot": "produce",
        "pepper": "produce",
        "broccoli": "produce",
        "spinach": "produce",
        "lettuce": "produce",
        "cabbage": "produce",
        "zucchini": "produce",
        "eggplant": "produce",
        "mushroom": "produce",
        "bean": "produce",
        "pea": "produce",
        "corn": "produce",
        "cucumber": "produce",
        "celery": "produce",
        "leek": "produce",
        "apple": "produce",
        "lemon": "produce",
        # Grains & Pasta
        "pasta": "grains",
        "rice": "grains",
        "bread": "grains",
        "flour": "grains",
        "noodle": "grains",
        "semolina": "grains",
        # Pantry
        "oil": "pantry",
        "vinegar": "pantry",
        "sugar": "pantry",
        "salt": "pantry",
        "spice": "pantry",
        "sauce": "pantry",
        "stock": "pantry",
        "broth": "pantry",
    }

    def __init__(self, session: Session):
        self.session = session

    def generate_shopping_list(self, plan: WeeklyPlan) -> ShoppingList:
        """Generate a shopping list from a weekly plan.

        Note: Since we don't have detailed ingredient data,
        this creates a list based on meal names as a reminder.
        """
        meals = []
        seen_meals: set[int] = set()

        for pm in plan.plan_meals:
            if pm.meal and pm.meal.id not in seen_meals:
                meals.append(pm.meal.name)
                seen_meals.add(pm.meal.id)

        # Create basic shopping items from meal names
        items: list[ShoppingItem] = []

        # Add each unique meal as a shopping reminder
        for meal_name in meals:
            category = self._categorize_meal(meal_name)
            items.append(
                ShoppingItem(
                    name=f"Ingredients for: {meal_name}",
                    meal_names=[meal_name],
                    category=category,
                )
            )

        return ShoppingList(
            week=plan.week_number,
            year=plan.year,
            start_date=plan.start_date,
            items=items,
            meals=meals,
        )

    def _categorize_meal(self, meal_name: str) -> str:
        """Categorize a meal based on its name."""
        name_lower = meal_name.lower()

        if any(word in name_lower for word in ["soup", "leves"]):
            return "soups"
        if any(word in name_lower for word in ["pasta", "tészta", "spaghetti", "penne"]):
            return "pasta dishes"
        if any(word in name_lower for word in ["chicken", "csirke"]):
            return "poultry dishes"
        if any(word in name_lower for word in ["fish", "hal", "salmon", "tuna"]):
            return "fish dishes"
        if any(word in name_lower for word in ["beef", "pork", "meat", "hús", "bacon"]):
            return "meat dishes"
        if any(word in name_lower for word in ["salad", "saláta"]):
            return "salads"
        if any(word in name_lower for word in ["vegetable", "veg", "zöldség"]):
            return "vegetable dishes"

        return "main dishes"

    def export_plan_json(self, plan: WeeklyPlan) -> str:
        """Export a plan as JSON."""
        meals_data = []
        for pm in plan.plan_meals:
            if pm.meal:
                meals_data.append({
                    "id": pm.meal.id,
                    "name": pm.meal.name,
                    "nev": pm.meal.nev,
                    "type": pm.meal.meal_type,
                    "cuisine": pm.meal.cuisine,
                    "has_meat": pm.meal.has_meat,
                    "is_vegetarian": pm.meal.is_vegetarian,
                    "is_leftover": pm.is_leftover,
                })

        data = {
            "week": plan.week_number,
            "year": plan.year,
            "start_date": plan.start_date.isoformat(),
            "meals": meals_data,
            "exported_at": datetime.now().isoformat(),
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def export_plan_markdown(self, plan: WeeklyPlan, lang: str = "en") -> str:
        """Export a plan as markdown."""
        lines = [
            f"# Weekly Meal Plan - Week {plan.week_number}, {plan.year}",
            f"*Starting: {plan.start_date}*",
            "",
        ]

        # Separate by type
        soups = []
        mains = []
        others = []

        for pm in plan.plan_meals:
            if pm.meal:
                if pm.meal.meal_type == "soup":
                    soups.append(pm)
                elif pm.meal.meal_type in ("main_course", "pasta", "dinner"):
                    mains.append(pm)
                else:
                    others.append(pm)

        if soups:
            lines.append("## Soups")
            for pm in soups:
                name = pm.meal.nev if lang == "hu" else pm.meal.name
                leftover = " *(leftover)*" if pm.is_leftover else ""
                cuisine = f" - {pm.meal.cuisine}" if pm.meal.cuisine else ""
                lines.append(f"- {name}{cuisine}{leftover}")
            lines.append("")

        if mains:
            lines.append("## Main Courses")
            for pm in mains:
                name = pm.meal.nev if lang == "hu" else pm.meal.name
                leftover = " *(leftover)*" if pm.is_leftover else ""
                cuisine = f" - {pm.meal.cuisine}" if pm.meal.cuisine else ""
                meat = " [M]" if pm.meal.has_meat else ""
                lines.append(f"- {name}{cuisine}{meat}{leftover}")
            lines.append("")

        if others:
            lines.append("## Other")
            for pm in others:
                name = pm.meal.nev if lang == "hu" else pm.meal.name
                leftover = " *(leftover)*" if pm.is_leftover else ""
                lines.append(f"- {name} ({pm.meal.meal_type}){leftover}")
            lines.append("")

        # Stats
        total = len([pm for pm in plan.plan_meals if pm.meal])
        meat_count = len([pm for pm in plan.plan_meals if pm.meal and pm.meal.has_meat])
        lines.append("---")
        lines.append(f"*Total: {total} meals ({len(soups)} soups, {len(mains)} mains, {meat_count} with meat)*")

        return "\n".join(lines)

    def export_plan_ics(self, plan: WeeklyPlan, meal_time: str = "12:00") -> str:
        """Export a plan as ICS calendar file.

        Creates one event per day with that day's meals.
        """
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Carmy//Meal Planner//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:Meals Week {plan.week_number}",
        ]

        # Group meals by nothing specific (we don't have day info)
        # So create a single event for the week
        meals = [pm.meal.name for pm in plan.plan_meals if pm.meal]
        soups = [pm.meal.name for pm in plan.plan_meals if pm.meal and pm.meal.meal_type == "soup"]
        mains = [pm.meal.name for pm in plan.plan_meals if pm.meal and pm.meal.meal_type in ("main_course", "pasta", "dinner")]

        # Create weekly summary event
        event_date = plan.start_date
        dtstart = event_date.strftime("%Y%m%d")
        dtend = (event_date + timedelta(days=7)).strftime("%Y%m%d")

        description = f"Soups: {', '.join(soups)}\\nMain courses: {', '.join(mains)}"
        summary = f"Week {plan.week_number} Meal Plan"

        lines.extend([
            "BEGIN:VEVENT",
            f"DTSTART;VALUE=DATE:{dtstart}",
            f"DTEND;VALUE=DATE:{dtend}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            f"UID:carmy-week-{plan.year}-{plan.week_number}@carmy",
            f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
            "END:VEVENT",
        ])

        lines.append("END:VCALENDAR")
        return "\n".join(lines)

    def export_plan_csv(self, plan: WeeklyPlan) -> str:
        """Export a plan as CSV."""
        lines = ["name,nev,type,cuisine,has_meat,is_vegetarian,is_leftover"]

        for pm in plan.plan_meals:
            if pm.meal:
                lines.append(
                    f'"{pm.meal.name}","{pm.meal.nev}","{pm.meal.meal_type}",'
                    f'"{pm.meal.cuisine or ""}",{pm.meal.has_meat},{pm.meal.is_vegetarian},{pm.is_leftover}'
                )

        return "\n".join(lines)


# ============== V2 EXPORT SERVICE ==============


@dataclass
class V2ShoppingItem:
    """Shopping list item for v2 week slots."""

    name: str
    category: str = "other"
    meal_names: list[str] = field(default_factory=list)
    source: str = "fresh"  # fresh, leftover
    date: Optional[date] = None


@dataclass
class V2ShoppingList:
    """Shopping list generated from v2 week skeleton."""

    year: int
    week_number: int
    start_date: date
    end_date: date
    items: list[V2ShoppingItem] = field(default_factory=list)
    fresh_meals: list[str] = field(default_factory=list)
    leftover_meals: list[str] = field(default_factory=list)

    def to_text(self) -> str:
        """Export as plain text."""
        lines = [
            f"Shopping List - Week {self.week_number}, {self.year}",
            f"{self.start_date.strftime('%b %d')} - {self.end_date.strftime('%b %d')}",
            "",
            "MEALS TO COOK FRESH:",
        ]

        for meal in self.fresh_meals:
            lines.append(f"  * {meal}")

        lines.extend(["", "SHOPPING LIST:", ""])

        # Group by category
        by_category: dict[str, list[V2ShoppingItem]] = {}
        for item in self.items:
            by_category.setdefault(item.category, []).append(item)

        for category in sorted(by_category.keys()):
            lines.append(f"{category.upper()}:")
            for item in by_category[category]:
                lines.append(f"  [ ] {item.name}")
            lines.append("")

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Export as markdown."""
        lines = [
            f"# Shopping List - Week {self.week_number}",
            f"*{self.start_date.strftime('%B %d')} - {self.end_date.strftime('%B %d, %Y')}*",
            "",
            "## Meals to Cook Fresh",
        ]

        for meal in self.fresh_meals:
            lines.append(f"- {meal}")

        lines.extend(["", "## Shopping List"])

        # Group by category
        by_category: dict[str, list[V2ShoppingItem]] = {}
        for item in self.items:
            by_category.setdefault(item.category, []).append(item)

        for category in sorted(by_category.keys()):
            lines.append(f"\n### {category.title()}")
            for item in by_category[category]:
                lines.append(f"- [ ] {item.name}")

        return "\n".join(lines)


class V2ExportService:
    """Export service for v2 week skeletons and month plans."""

    def __init__(self, session: Session):
        self.session = session

    def generate_week_ics(self, skeleton: "WeekSkeleton") -> str:
        """Generate ICS calendar for a week skeleton.

        Creates events for each day with dinner/lunch meals.
        """
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Carmy//Meal Planner v2//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:Carmy Week {skeleton.week_number}",
        ]

        # Group slots by date
        slots_by_date: dict[date, list] = {}
        for slot in skeleton.meal_slots:
            slots_by_date.setdefault(slot.date, []).append(slot)

        # Create event for each day
        for slot_date in sorted(slots_by_date.keys()):
            slots = slots_by_date[slot_date]

            # Build description
            dinner_slots = [s for s in slots if s.meal_time == "dinner" and s.notes != "Soup"]
            lunch_slots = [s for s in slots if s.meal_time == "lunch" and s.notes != "Soup"]
            soup_slots = [s for s in slots if s.notes == "Soup"]

            desc_parts = []
            if dinner_slots:
                dinner_names = [s.meal.name if s.meal else "Light meal" for s in dinner_slots]
                sources = [f"({s.source})" if s.source != "fresh" else "" for s in dinner_slots]
                desc_parts.append(f"Dinner: {', '.join(f'{n} {src}'.strip() for n, src in zip(dinner_names, sources))}")

            if lunch_slots:
                lunch_names = [s.meal.name if s.meal else "Light meal" for s in lunch_slots]
                desc_parts.append(f"Lunch: {', '.join(lunch_names)}")

            if soup_slots:
                soup_names = [s.meal.name if s.meal else "Soup" for s in soup_slots]
                desc_parts.append(f"Soup: {', '.join(soup_names)}")

            description = "\\n".join(desc_parts)

            # Summary (main dinner)
            main_meal = dinner_slots[0].meal.name if dinner_slots and dinner_slots[0].meal else "Light meal"
            summary = f"Dinner: {main_meal}"

            # Create event
            dtstart = slot_date.strftime("%Y%m%d")
            uid = f"carmy-v2-{skeleton.year}-{skeleton.week_number}-{slot_date.isoformat()}@carmy"

            lines.extend([
                "BEGIN:VEVENT",
                f"DTSTART;VALUE=DATE:{dtstart}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{description}",
                f"UID:{uid}",
                f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                "END:VEVENT",
            ])

        lines.append("END:VCALENDAR")
        return "\n".join(lines)

    def generate_month_ics(self, month_plan: "MonthPlan") -> str:
        """Generate ICS calendar for an entire month plan."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Carmy//Meal Planner v2//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:Carmy {month_plan.year}-{month_plan.month:02d}",
        ]

        # Iterate through all weeks
        for skeleton in month_plan.week_skeletons:
            # Group slots by date
            slots_by_date: dict[date, list] = {}
            for slot in skeleton.meal_slots:
                slots_by_date.setdefault(slot.date, []).append(slot)

            for slot_date in sorted(slots_by_date.keys()):
                slots = slots_by_date[slot_date]

                dinner_slots = [s for s in slots if s.meal_time == "dinner" and s.notes != "Soup"]
                main_meal = dinner_slots[0].meal.name if dinner_slots and dinner_slots[0].meal else "Light meal"

                dtstart = slot_date.strftime("%Y%m%d")
                uid = f"carmy-month-{month_plan.year}-{month_plan.month}-{slot_date.isoformat()}@carmy"

                lines.extend([
                    "BEGIN:VEVENT",
                    f"DTSTART;VALUE=DATE:{dtstart}",
                    f"SUMMARY:Dinner: {main_meal}",
                    f"UID:{uid}",
                    f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                    "END:VEVENT",
                ])

        lines.append("END:VCALENDAR")
        return "\n".join(lines)

    def generate_shopping_list(self, skeleton: "WeekSkeleton") -> V2ShoppingList:
        """Generate shopping list from week skeleton.

        Only includes fresh meals (not leftovers).
        """
        shopping_list = V2ShoppingList(
            year=skeleton.year,
            week_number=skeleton.week_number,
            start_date=skeleton.start_date,
            end_date=skeleton.end_date,
        )

        seen_meals: set[int] = set()

        for slot in skeleton.meal_slots:
            if not slot.meal:
                continue

            # Only include fresh meals for shopping
            if slot.source == "fresh":
                if slot.meal.id not in seen_meals:
                    shopping_list.fresh_meals.append(slot.meal.name)
                    seen_meals.add(slot.meal.id)

                    # Create shopping item for this meal
                    category = self._categorize_meal(slot.meal)
                    shopping_list.items.append(V2ShoppingItem(
                        name=f"Ingredients for: {slot.meal.name}",
                        category=category,
                        meal_names=[slot.meal.name],
                        source="fresh",
                        date=slot.date,
                    ))
            elif slot.source == "leftover":
                if slot.meal.id not in seen_meals:
                    shopping_list.leftover_meals.append(slot.meal.name)

        return shopping_list

    def _categorize_meal(self, meal: Meal) -> str:
        """Categorize a meal for shopping list organization."""
        if meal.meal_type == "soup":
            return "soups"
        if meal.meal_type in ("pasta", "noodles"):
            return "pasta dishes"
        if meal.has_meat:
            return "meat dishes"
        if meal.is_vegetarian:
            return "vegetarian"
        return "main dishes"

    def generate_week_json(self, skeleton: "WeekSkeleton") -> str:
        """Export week skeleton as JSON."""
        data = {
            "year": skeleton.year,
            "week_number": skeleton.week_number,
            "start_date": skeleton.start_date.isoformat(),
            "end_date": skeleton.end_date.isoformat(),
            "status": skeleton.status,
            "cooking_events": [],
            "meal_slots": [],
            "exported_at": datetime.now().isoformat(),
        }

        for event in skeleton.cooking_events:
            data["cooking_events"].append({
                "id": event.id,
                "cook_date": event.cook_date.isoformat(),
                "meal_id": event.meal_id,
                "meal_name": event.meal.name if event.meal else None,
                "serves_days": event.serves_days,
                "event_type": event.event_type,
                "effort_level": event.effort_level,
            })

        for slot in skeleton.meal_slots:
            data["meal_slots"].append({
                "id": slot.id,
                "date": slot.date.isoformat(),
                "meal_time": slot.meal_time,
                "meal_id": slot.meal_id,
                "meal_name": slot.meal.name if slot.meal else None,
                "source": slot.source,
                "leftover_day": slot.leftover_day,
                "status": slot.status,
            })

        return json.dumps(data, indent=2, ensure_ascii=False)

    def generate_share_token(self, skeleton: "WeekSkeleton") -> str:
        """Generate a share token for a week skeleton.

        This creates a deterministic but non-guessable token.
        """
        # Create a hash from skeleton data
        data = f"{skeleton.year}-{skeleton.week_number}-{skeleton.id}-carmy-share"
        token = hashlib.sha256(data.encode()).hexdigest()[:16]
        return token

    def generate_week_markdown(self, skeleton: "WeekSkeleton") -> str:
        """Export week skeleton as markdown."""
        lines = [
            f"# Week {skeleton.week_number}, {skeleton.year}",
            f"*{skeleton.start_date.strftime('%B %d')} - {skeleton.end_date.strftime('%B %d, %Y')}*",
            "",
        ]

        # Group by date
        slots_by_date: dict[date, list] = {}
        for slot in skeleton.meal_slots:
            slots_by_date.setdefault(slot.date, []).append(slot)

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for slot_date in sorted(slots_by_date.keys()):
            day_name = day_names[slot_date.weekday()]
            lines.append(f"## {day_name}, {slot_date.strftime('%b %d')}")

            slots = slots_by_date[slot_date]
            for slot in sorted(slots, key=lambda s: (s.meal_time != "dinner", s.notes == "Soup")):
                meal_name = slot.meal.name if slot.meal else "Light meal"
                source_badge = ""
                if slot.source == "leftover":
                    source_badge = f" *(leftover day {slot.leftover_day})*"
                elif slot.source == "light":
                    source_badge = " *(light)*"

                soup_badge = " [Soup]" if slot.notes == "Soup" else ""
                time_label = slot.meal_time.capitalize()

                lines.append(f"- **{time_label}**: {meal_name}{soup_badge}{source_badge}")

            lines.append("")

        return "\n".join(lines)

    def generate_week_html(self, skeleton: "WeekSkeleton") -> str:
        """Export week skeleton as standalone HTML for printing/sharing."""
        # Group by date
        slots_by_date: dict[date, list] = {}
        for slot in skeleton.meal_slots:
            slots_by_date.setdefault(slot.date, []).append(slot)

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        days_html = []
        for slot_date in sorted(slots_by_date.keys()):
            day_name = day_names[slot_date.weekday()]
            slots = slots_by_date[slot_date]

            meals_html = []
            for slot in sorted(slots, key=lambda s: (s.meal_time != "dinner", s.notes == "Soup")):
                meal_name = slot.meal.name if slot.meal else "Light meal"
                source_class = slot.source
                time_label = slot.meal_time.capitalize()

                meals_html.append(f'''
                    <div class="meal {source_class}">
                        <span class="time">{time_label}</span>
                        <span class="name">{meal_name}</span>
                    </div>
                ''')

            days_html.append(f'''
                <div class="day">
                    <div class="day-header">{day_name} {slot_date.day}</div>
                    <div class="meals">{''.join(meals_html)}</div>
                </div>
            ''')

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Week {skeleton.week_number} Meal Plan</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #e67e22; }}
        .week-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .day {{ border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
        .day-header {{ background: #e67e22; color: white; padding: 10px; font-weight: bold; }}
        .meals {{ padding: 10px; }}
        .meal {{ padding: 8px; margin-bottom: 8px; border-radius: 4px; border-left: 3px solid #ccc; }}
        .meal.fresh {{ border-left-color: #22c55e; background: #f0fdf4; }}
        .meal.leftover {{ border-left-color: #eab308; background: #fefce8; }}
        .meal.light {{ border-left-color: #3b82f6; background: #eff6ff; }}
        .time {{ font-size: 0.75em; color: #666; text-transform: uppercase; display: block; }}
        .name {{ font-weight: 500; }}
        @media print {{ body {{ padding: 0; }} .day {{ break-inside: avoid; }} }}
    </style>
</head>
<body>
    <h1>Week {skeleton.week_number}, {skeleton.year}</h1>
    <p>{skeleton.start_date.strftime('%B %d')} - {skeleton.end_date.strftime('%B %d, %Y')}</p>
    <div class="week-grid">{''.join(days_html)}</div>
    <p style="margin-top: 20px; color: #666; font-size: 0.875em;">Generated by Carmy Meal Planner</p>
</body>
</html>'''

        return html
