"""Rules engine for validating weekly meal plans."""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from carmy.models.meal import Meal
    from carmy.models.plan import WeeklyPlan


class RuleSeverity(str, Enum):
    """Severity level for rule violations."""

    ERROR = "error"  # Must be fixed
    WARNING = "warning"  # Should be addressed
    INFO = "info"  # Suggestion


class RuleType(str, Enum):
    """Types of validation rules."""

    QUOTA = "quota"
    TASTE_DIVERSITY = "taste_diversity"
    MEAT_LIMIT = "meat_limit"
    DUPLICATE = "duplicate"
    CUISINE_ROTATION = "cuisine_rotation"


@dataclass
class RuleViolation:
    """A single rule violation."""

    rule_type: RuleType
    severity: RuleSeverity
    message: str
    message_hu: str
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        icon = {"error": "[X]", "warning": "[!]", "info": "[i]"}[self.severity.value]
        return f"{icon} {self.message}"


@dataclass
class ValidationResult:
    """Result of validating a weekly plan."""

    plan_year: int
    plan_week: int
    violations: list[RuleViolation] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if plan has no errors (warnings allowed)."""
        return not any(v.severity == RuleSeverity.ERROR for v in self.violations)

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == RuleSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == RuleSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == RuleSeverity.INFO)


class RulesEngine:
    """Engine for validating weekly meal plans against planning rules."""

    def __init__(
        self,
        soups_per_week: int = 2,
        main_courses_per_week: int = 4,
        max_meat_dishes: int = 3,
        max_same_cuisine: int = 2,
    ):
        self.soups_per_week = soups_per_week
        self.main_courses_per_week = main_courses_per_week
        self.max_meat_dishes = max_meat_dishes
        self.max_same_cuisine = max_same_cuisine

    def validate(self, plan: "WeeklyPlan") -> ValidationResult:
        """Validate a weekly plan against all rules.

        Args:
            plan: The weekly plan to validate

        Returns:
            ValidationResult with all violations found
        """
        result = ValidationResult(
            plan_year=plan.year,
            plan_week=plan.week_number,
        )

        # Get all meals from the plan (excluding None meals)
        meals = [pm.meal for pm in plan.plan_meals if pm.meal is not None]
        unique_meals = self._get_unique_meals(plan)

        # Collect statistics
        result.stats = self._collect_stats(plan, meals, unique_meals)

        # Run all validation rules
        result.violations.extend(self._check_weekly_quota(plan, unique_meals))
        result.violations.extend(self._check_taste_diversity(meals))
        result.violations.extend(self._check_meat_limit(unique_meals))
        result.violations.extend(self._check_duplicates(plan))
        result.violations.extend(self._check_cuisine_rotation(unique_meals))

        return result

    def _get_unique_meals(self, plan: "WeeklyPlan") -> list["Meal"]:
        """Get unique meals from plan (excluding leftovers)."""
        seen_ids = set()
        unique = []
        for pm in plan.plan_meals:
            if pm.meal and pm.meal.id not in seen_ids and not pm.is_leftover:
                seen_ids.add(pm.meal.id)
                unique.append(pm.meal)
        return unique

    def _collect_stats(
        self, plan: "WeeklyPlan", meals: list["Meal"], unique_meals: list["Meal"]
    ) -> dict:
        """Collect statistics about the plan."""
        soups = [m for m in unique_meals if m.meal_type == "soup"]
        main_courses = [m for m in unique_meals if m.meal_type in ("main_course", "pasta", "dinner")]
        meat_dishes = [m for m in unique_meals if m.has_meat]

        cuisine_counts: dict[str, int] = {}
        for meal in unique_meals:
            if meal.cuisine:
                cuisine_counts[meal.cuisine] = cuisine_counts.get(meal.cuisine, 0) + 1

        return {
            "total_meals": len(meals),
            "unique_meals": len(unique_meals),
            "soups": len(soups),
            "main_courses": len(main_courses),
            "meat_dishes": len(meat_dishes),
            "vegetarian_dishes": len([m for m in unique_meals if m.is_vegetarian]),
            "cuisines": cuisine_counts,
            "leftover_count": sum(1 for pm in plan.plan_meals if pm.is_leftover),
        }

    def _check_weekly_quota(
        self, plan: "WeeklyPlan", unique_meals: list["Meal"]
    ) -> list[RuleViolation]:
        """Check if weekly quotas are met (2 soups, 4 mains)."""
        violations = []

        soups = [m for m in unique_meals if m.meal_type == "soup"]
        main_courses = [m for m in unique_meals if m.meal_type in ("main_course", "pasta", "dinner")]

        soup_count = len(soups)
        main_count = len(main_courses)

        # Check soup quota
        if soup_count < self.soups_per_week:
            violations.append(
                RuleViolation(
                    rule_type=RuleType.QUOTA,
                    severity=RuleSeverity.WARNING,
                    message=f"Only {soup_count} soup(s) planned, expected {self.soups_per_week}",
                    message_hu=f"Csak {soup_count} leves van tervezve, {self.soups_per_week} kellene",
                    details={"actual": soup_count, "expected": self.soups_per_week, "type": "soup"},
                )
            )
        elif soup_count > self.soups_per_week:
            violations.append(
                RuleViolation(
                    rule_type=RuleType.QUOTA,
                    severity=RuleSeverity.INFO,
                    message=f"{soup_count} soups planned (more than usual {self.soups_per_week})",
                    message_hu=f"{soup_count} leves van tervezve (több mint a szokásos {self.soups_per_week})",
                    details={"actual": soup_count, "expected": self.soups_per_week, "type": "soup"},
                )
            )

        # Check main course quota
        if main_count < self.main_courses_per_week:
            violations.append(
                RuleViolation(
                    rule_type=RuleType.QUOTA,
                    severity=RuleSeverity.WARNING,
                    message=f"Only {main_count} main course(s) planned, expected {self.main_courses_per_week}",
                    message_hu=f"Csak {main_count} főétel van tervezve, {self.main_courses_per_week} kellene",
                    details={"actual": main_count, "expected": self.main_courses_per_week, "type": "main"},
                )
            )

        return violations

    def _check_taste_diversity(self, meals: list["Meal"]) -> list[RuleViolation]:
        """Check for flavor base conflicts (e.g., broccoli soup + broccoli pasta)."""
        violations = []
        flavor_usage: dict[str, list[str]] = {}

        for meal in meals:
            for flavor in meal.flavor_bases:
                flavor_lower = flavor.lower()
                if flavor_lower not in flavor_usage:
                    flavor_usage[flavor_lower] = []
                if meal.name not in flavor_usage[flavor_lower]:
                    flavor_usage[flavor_lower].append(meal.name)

        # Check for conflicts
        for flavor, meal_names in flavor_usage.items():
            if len(meal_names) > 1:
                violations.append(
                    RuleViolation(
                        rule_type=RuleType.TASTE_DIVERSITY,
                        severity=RuleSeverity.WARNING,
                        message=f"Flavor conflict: '{flavor}' appears in {len(meal_names)} dishes: {', '.join(meal_names)}",
                        message_hu=f"Íz ütközés: '{flavor}' {len(meal_names)} ételben szerepel: {', '.join(meal_names)}",
                        details={"flavor": flavor, "meals": meal_names},
                    )
                )

        return violations

    def _check_meat_limit(self, unique_meals: list["Meal"]) -> list[RuleViolation]:
        """Check if meat dish limit is exceeded."""
        violations = []

        meat_dishes = [m for m in unique_meals if m.has_meat]
        meat_count = len(meat_dishes)

        if meat_count > self.max_meat_dishes:
            meal_names = [m.name for m in meat_dishes]
            violations.append(
                RuleViolation(
                    rule_type=RuleType.MEAT_LIMIT,
                    severity=RuleSeverity.WARNING,
                    message=f"Too many meat dishes: {meat_count} (max {self.max_meat_dishes}): {', '.join(meal_names)}",
                    message_hu=f"Túl sok húsos étel: {meat_count} (max {self.max_meat_dishes}): {', '.join(meal_names)}",
                    details={"actual": meat_count, "max": self.max_meat_dishes, "meals": meal_names},
                )
            )

        return violations

    def _check_duplicates(self, plan: "WeeklyPlan") -> list[RuleViolation]:
        """Check for same meal appearing twice in the same week (non-leftover)."""
        violations = []
        meal_occurrences: dict[int, list[str]] = {}

        for pm in plan.plan_meals:
            if pm.meal and not pm.is_leftover:
                meal_id = pm.meal.id
                day = pm.day_name if pm.day_of_week is not None else "unassigned"
                if meal_id not in meal_occurrences:
                    meal_occurrences[meal_id] = []
                meal_occurrences[meal_id].append(day)

        for meal_id, days in meal_occurrences.items():
            if len(days) > 1:
                # Find the meal name
                meal = next(pm.meal for pm in plan.plan_meals if pm.meal and pm.meal.id == meal_id)
                violations.append(
                    RuleViolation(
                        rule_type=RuleType.DUPLICATE,
                        severity=RuleSeverity.INFO,
                        message=f"'{meal.name}' appears {len(days)} times (not marked as leftover)",
                        message_hu=f"'{meal.nev}' {len(days)}-szer szerepel (nem maradékként jelölve)",
                        details={"meal": meal.name, "days": days},
                    )
                )

        return violations

    def _check_cuisine_rotation(self, unique_meals: list["Meal"]) -> list[RuleViolation]:
        """Check if any cuisine appears too many times."""
        violations = []
        cuisine_counts: dict[str, list[str]] = {}

        for meal in unique_meals:
            if meal.cuisine:
                cuisine = meal.cuisine
                if cuisine not in cuisine_counts:
                    cuisine_counts[cuisine] = []
                cuisine_counts[cuisine].append(meal.name)

        for cuisine, meal_names in cuisine_counts.items():
            if len(meal_names) > self.max_same_cuisine:
                violations.append(
                    RuleViolation(
                        rule_type=RuleType.CUISINE_ROTATION,
                        severity=RuleSeverity.INFO,
                        message=f"'{cuisine}' cuisine appears {len(meal_names)} times: {', '.join(meal_names)}",
                        message_hu=f"'{cuisine}' konyha {len(meal_names)}-szer szerepel: {', '.join(meal_names)}",
                        details={"cuisine": cuisine, "count": len(meal_names), "meals": meal_names},
                    )
                )

        return violations
