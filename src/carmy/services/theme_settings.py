"""Theme and settings system for month planning.

This module defines:
- Theme presets with their effects on meal selection
- Settings validation and serialization
- Theme application logic
"""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ThemeDefinition:
    """Definition of a planning theme."""

    name: str
    description: str
    icon: str

    # Slider modifications (added to base values)
    meat_delta: float = 0.0
    fish_delta: float = 0.0
    veggie_delta: float = 0.0
    new_recipes_delta: float = 0.0
    cuisine_balance_delta: float = 0.0  # negative = more Hungarian

    # Special mode flags
    lent_mode: bool = False
    batch_cooking: bool = False

    # Quota modifications
    soups_per_week: int | None = None
    max_meat_per_week: int | None = None

    # Cuisine preferences
    preferred_cuisines: list[str] = field(default_factory=list)
    avoided_cuisines: list[str] = field(default_factory=list)

    # Meal type preferences
    preferred_meal_types: list[str] = field(default_factory=list)
    avoided_meal_types: list[str] = field(default_factory=list)

    # Keywords for meal selection boost
    boost_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


# Theme definitions
THEMES: dict[str, ThemeDefinition] = {
    "comfort": ThemeDefinition(
        name="comfort",
        description="Hearty, warming meals for cold days or tough times",
        icon="🏠",
        meat_delta=0.2,
        cuisine_balance_delta=-0.2,  # More Hungarian
        batch_cooking=True,
        preferred_meal_types=["main_course", "fozelek"],
        boost_keywords=["stew", "gulash", "paprikas", "pot roast", "ragu"],
    ),
    "light": ThemeDefinition(
        name="light",
        description="Fresh, lighter meals for warm weather or healthy eating",
        icon="🥗",
        meat_delta=-0.2,
        veggie_delta=0.3,
        fish_delta=0.1,
        preferred_meal_types=["pasta", "salad"],
        avoided_meal_types=["fozelek"],
        boost_keywords=["salad", "grilled", "fresh", "light"],
    ),
    "seafood": ThemeDefinition(
        name="seafood",
        description="Focus on fish and seafood dishes",
        icon="🐟",
        fish_delta=0.4,
        meat_delta=-0.2,
        max_meat_per_week=2,
        preferred_cuisines=["mediterranean", "asian", "japanese"],
        boost_keywords=["fish", "shrimp", "salmon", "seafood", "tuna"],
    ),
    "budget": ThemeDefinition(
        name="budget",
        description="Economical cooking with pantry staples",
        icon="💰",
        new_recipes_delta=-0.3,  # Stick to known recipes
        batch_cooking=True,
        meat_delta=-0.1,  # Less expensive meats
        preferred_meal_types=["pasta", "fozelek", "soup"],
        boost_keywords=["beans", "lentil", "potato", "rice", "eggs"],
    ),
    "guests": ThemeDefinition(
        name="guests",
        description="Impressive meals for entertaining",
        icon="🎉",
        new_recipes_delta=0.2,
        meat_delta=0.1,
        cuisine_balance_delta=0.2,  # More international
        preferred_cuisines=["mediterranean", "french", "italian"],
        boost_keywords=["roast", "special", "elegant"],
    ),
    "lent": ThemeDefinition(
        name="lent",
        description="Traditional Lenten fare - meatless Fridays",
        icon="✝️",
        lent_mode=True,
        meat_delta=-0.3,
        fish_delta=0.2,
        veggie_delta=0.2,
        cuisine_balance_delta=-0.2,  # More Hungarian
        max_meat_per_week=2,
        boost_keywords=["fish", "vegetarian", "beans", "lentil"],
    ),
    "pantry_clearing": ThemeDefinition(
        name="pantry_clearing",
        description="Use up what you have before shopping",
        icon="🗄️",
        new_recipes_delta=-0.4,  # Familiar recipes
        batch_cooking=False,  # Smaller portions
        boost_keywords=["pantry", "canned", "frozen", "leftover"],
    ),
    "batch_cooking": ThemeDefinition(
        name="batch_cooking",
        description="Cook once, eat multiple days",
        icon="🍲",
        batch_cooking=True,
        meat_delta=0.1,  # Batch dishes often have meat
        preferred_meal_types=["main_course", "fozelek"],
        boost_keywords=["stew", "roast", "ragu", "batch"],
    ),
}


@dataclass
class MonthSettingsV2:
    """Enhanced settings for month plan generation.

    Supports serialization to/from JSON for database storage.
    """

    # Dietary sliders (0.0 - 1.0)
    meat_level: float = 0.5
    fish_level: float = 0.3
    veggie_level: float = 0.5
    new_recipes: float = 0.3
    cuisine_balance: float = 0.5  # 0 = all Hungarian, 1 = all international

    # Special modes
    lent_mode: bool = False
    batch_cooking: bool = False
    sales_aware: bool = True

    # Week configuration
    big_cook_days: list[int] = field(default_factory=lambda: [5])  # Saturday
    mid_week_cook_days: list[int] = field(default_factory=lambda: [1, 2])  # Tue, Wed
    fun_food_days: list[int] = field(default_factory=lambda: [4])  # Friday

    # Quotas per week
    soups_per_week: int = 2
    main_courses_per_week: int = 4
    max_meat_per_week: int = 3

    # Cuisine preferences
    preferred_cuisines: list[str] = field(default_factory=list)
    avoided_cuisines: list[str] = field(default_factory=list)

    # Meal type preferences
    preferred_meal_types: list[str] = field(default_factory=list)
    avoided_meal_types: list[str] = field(default_factory=list)

    # Keywords for boosting
    boost_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "meat_level": self.meat_level,
            "fish_level": self.fish_level,
            "veggie_level": self.veggie_level,
            "new_recipes": self.new_recipes,
            "cuisine_balance": self.cuisine_balance,
            "lent_mode": self.lent_mode,
            "batch_cooking": self.batch_cooking,
            "sales_aware": self.sales_aware,
            "big_cook_days": self.big_cook_days,
            "mid_week_cook_days": self.mid_week_cook_days,
            "fun_food_days": self.fun_food_days,
            "soups_per_week": self.soups_per_week,
            "main_courses_per_week": self.main_courses_per_week,
            "max_meat_per_week": self.max_meat_per_week,
            "preferred_cuisines": self.preferred_cuisines,
            "avoided_cuisines": self.avoided_cuisines,
            "preferred_meal_types": self.preferred_meal_types,
            "avoided_meal_types": self.avoided_meal_types,
            "boost_keywords": self.boost_keywords,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MonthSettingsV2":
        """Create settings from dictionary."""
        return cls(
            meat_level=data.get("meat_level", 0.5),
            fish_level=data.get("fish_level", 0.3),
            veggie_level=data.get("veggie_level", 0.5),
            new_recipes=data.get("new_recipes", 0.3),
            cuisine_balance=data.get("cuisine_balance", 0.5),
            lent_mode=data.get("lent_mode", False),
            batch_cooking=data.get("batch_cooking", False),
            sales_aware=data.get("sales_aware", True),
            big_cook_days=data.get("big_cook_days", [5]),
            mid_week_cook_days=data.get("mid_week_cook_days", [1, 2]),
            fun_food_days=data.get("fun_food_days", [4]),
            soups_per_week=data.get("soups_per_week", 2),
            main_courses_per_week=data.get("main_courses_per_week", 4),
            max_meat_per_week=data.get("max_meat_per_week", 3),
            preferred_cuisines=data.get("preferred_cuisines", []),
            avoided_cuisines=data.get("avoided_cuisines", []),
            preferred_meal_types=data.get("preferred_meal_types", []),
            avoided_meal_types=data.get("avoided_meal_types", []),
            boost_keywords=data.get("boost_keywords", []),
        )

    def apply_theme(self, theme_name: str) -> "MonthSettingsV2":
        """Apply a theme to these settings, returning modified copy."""
        if theme_name not in THEMES:
            return self

        theme = THEMES[theme_name]

        # Clamp helper
        def clamp(val: float) -> float:
            return max(0.0, min(1.0, val))

        # Apply deltas
        new_settings = MonthSettingsV2(
            meat_level=clamp(self.meat_level + theme.meat_delta),
            fish_level=clamp(self.fish_level + theme.fish_delta),
            veggie_level=clamp(self.veggie_level + theme.veggie_delta),
            new_recipes=clamp(self.new_recipes + theme.new_recipes_delta),
            cuisine_balance=clamp(self.cuisine_balance + theme.cuisine_balance_delta),
            lent_mode=self.lent_mode or theme.lent_mode,
            batch_cooking=self.batch_cooking or theme.batch_cooking,
            sales_aware=self.sales_aware,
            big_cook_days=self.big_cook_days.copy(),
            mid_week_cook_days=self.mid_week_cook_days.copy(),
            fun_food_days=self.fun_food_days.copy(),
            soups_per_week=theme.soups_per_week or self.soups_per_week,
            main_courses_per_week=self.main_courses_per_week,
            max_meat_per_week=theme.max_meat_per_week or self.max_meat_per_week,
            preferred_cuisines=list(set(self.preferred_cuisines + theme.preferred_cuisines)),
            avoided_cuisines=list(set(self.avoided_cuisines + theme.avoided_cuisines)),
            preferred_meal_types=list(set(self.preferred_meal_types + theme.preferred_meal_types)),
            avoided_meal_types=list(set(self.avoided_meal_types + theme.avoided_meal_types)),
            boost_keywords=list(set(self.boost_keywords + theme.boost_keywords)),
        )

        return new_settings

    def validate(self) -> list[str]:
        """Validate settings, returning list of errors."""
        errors = []

        # Check slider ranges
        for name, value in [
            ("meat_level", self.meat_level),
            ("fish_level", self.fish_level),
            ("veggie_level", self.veggie_level),
            ("new_recipes", self.new_recipes),
            ("cuisine_balance", self.cuisine_balance),
        ]:
            if not 0.0 <= value <= 1.0:
                errors.append(f"{name} must be between 0.0 and 1.0")

        # Check quotas
        if self.soups_per_week < 0 or self.soups_per_week > 7:
            errors.append("soups_per_week must be between 0 and 7")
        if self.main_courses_per_week < 0 or self.main_courses_per_week > 7:
            errors.append("main_courses_per_week must be between 0 and 7")
        if self.max_meat_per_week < 0 or self.max_meat_per_week > 7:
            errors.append("max_meat_per_week must be between 0 and 7")

        # Check day configurations
        for day in self.big_cook_days + self.mid_week_cook_days + self.fun_food_days:
            if not 0 <= day <= 6:
                errors.append(f"Invalid day of week: {day}")

        return errors

    def describe(self) -> dict[str, str]:
        """Get human-readable descriptions of current settings."""
        descriptions = {}

        # Meat level
        if self.meat_level < 0.3:
            descriptions["diet"] = "Mostly vegetarian"
        elif self.meat_level > 0.7:
            descriptions["diet"] = "Meat-heavy"
        else:
            descriptions["diet"] = "Balanced meat/veggie"

        # Fish level
        if self.fish_level > 0.5:
            descriptions["fish"] = "Fish-focused"
        elif self.fish_level < 0.2:
            descriptions["fish"] = "Minimal fish"

        # Cuisine balance
        if self.cuisine_balance < 0.3:
            descriptions["cuisine"] = "Traditional Hungarian"
        elif self.cuisine_balance > 0.7:
            descriptions["cuisine"] = "International variety"
        else:
            descriptions["cuisine"] = "Mix of cuisines"

        # Special modes
        modes = []
        if self.lent_mode:
            modes.append("Lent (meatless Fridays)")
        if self.batch_cooking:
            modes.append("Batch cooking")
        if modes:
            descriptions["modes"] = ", ".join(modes)

        return descriptions


def get_theme(name: str) -> ThemeDefinition | None:
    """Get a theme definition by name."""
    return THEMES.get(name)


def list_themes() -> list[ThemeDefinition]:
    """Get all available themes."""
    return list(THEMES.values())


def get_theme_names() -> list[str]:
    """Get list of theme names."""
    return list(THEMES.keys())
