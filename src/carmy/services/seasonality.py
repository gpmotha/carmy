"""Seasonality service for seasonal meal planning."""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from carmy.models.meal import Meal


@dataclass
class SeasonalScore:
    """Seasonality score for a meal."""

    meal_id: int
    meal_name: str
    score: float  # 0.0 to 1.0
    season: str
    matching_ingredients: list[str]
    off_season_ingredients: list[str]

    @property
    def is_seasonal(self) -> bool:
        """Check if meal is considered seasonal (score >= 0.5)."""
        return self.score >= 0.5

    @property
    def rating(self) -> str:
        """Get a human-readable rating."""
        if self.score >= 0.8:
            return "Excellent"
        elif self.score >= 0.6:
            return "Good"
        elif self.score >= 0.4:
            return "Fair"
        elif self.score >= 0.2:
            return "Poor"
        return "Off-season"


def get_current_season(ref_date: date | None = None) -> str:
    """Get the current season based on date.

    Args:
        ref_date: Reference date (defaults to today)

    Returns:
        Season name: spring, summer, autumn, winter
    """
    if ref_date is None:
        ref_date = date.today()

    month = ref_date.month

    if month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    elif month in (9, 10, 11):
        return "autumn"
    else:
        return "winter"


class SeasonalityService:
    """Service for calculating meal seasonality scores."""

    def __init__(self, data_path: Path | str | None = None):
        """Initialize the seasonality service.

        Args:
            data_path: Path to seasonal_ingredients.json file
        """
        if data_path is None:
            # Default to data/seasonal_ingredients.json relative to project
            data_path = Path(__file__).parent.parent.parent.parent / "data" / "seasonal_ingredients.json"

        self.data_path = Path(data_path)
        self._data: dict | None = None

    @property
    def data(self) -> dict:
        """Lazy load seasonal ingredients data."""
        if self._data is None:
            if self.data_path.exists():
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                # Fallback minimal data
                self._data = {"hungary": {}}
        return self._data

    def get_seasonal_ingredients(
        self,
        season: str,
        region: str = "hungary",
    ) -> set[str]:
        """Get all seasonal ingredients for a season.

        Args:
            season: Season name (spring, summer, autumn, winter)
            region: Region for ingredient data

        Returns:
            Set of ingredient names
        """
        ingredients = set()
        region_data = self.data.get(region, {})
        season_data = region_data.get(season, {})

        for category in ["vegetables", "fruits", "herbs", "proteins", "pantry"]:
            ingredients.update(season_data.get(category, []))

        # Always include year_round ingredients
        year_round = region_data.get("year_round", {})
        for category in ["vegetables", "proteins", "pantry"]:
            ingredients.update(year_round.get(category, []))

        return ingredients

    def score_meal(
        self,
        meal: "Meal",
        season: str | None = None,
        ref_date: date | None = None,
    ) -> SeasonalScore:
        """Calculate seasonality score for a meal.

        Args:
            meal: The meal to score
            season: Season to score against (defaults to current)
            ref_date: Reference date for season detection

        Returns:
            SeasonalScore with details
        """
        if season is None:
            season = get_current_season(ref_date)

        # Get seasonal ingredients
        seasonal_ingredients = self.get_seasonal_ingredients(season)

        # Check meal's explicit seasonality attribute
        if meal.seasonality and meal.seasonality != "year_round":
            # If meal has explicit season set, use it
            if meal.seasonality == season:
                return SeasonalScore(
                    meal_id=meal.id,
                    meal_name=meal.name,
                    score=1.0,
                    season=season,
                    matching_ingredients=[],
                    off_season_ingredients=[],
                )
            else:
                return SeasonalScore(
                    meal_id=meal.id,
                    meal_name=meal.name,
                    score=0.2,  # Off-season penalty
                    season=season,
                    matching_ingredients=[],
                    off_season_ingredients=[],
                )

        # Check meal name for seasonal ingredients
        meal_name_lower = meal.name.lower()
        nev_lower = meal.nev.lower() if meal.nev else ""

        matching = []
        off_season = []

        # Check all seasons' ingredients against meal name
        all_seasonal = set()
        for s in ["spring", "summer", "autumn", "winter"]:
            if s != season:
                s_ingredients = self.get_seasonal_ingredients(s)
                all_seasonal.update(s_ingredients)

        for ingredient in seasonal_ingredients:
            if ingredient in meal_name_lower or ingredient in nev_lower:
                matching.append(ingredient)

        # Check for off-season specific ingredients
        for ingredient in all_seasonal - seasonal_ingredients:
            if ingredient in meal_name_lower or ingredient in nev_lower:
                # Only flag strongly seasonal items
                strong_seasonal = [
                    "asparagus", "strawberry", "rhubarb",  # spring
                    "watermelon", "corn", "peach", "cherry",  # summer
                    "pumpkin", "squash", "mushroom",  # autumn
                    "citrus", "orange",  # winter
                ]
                if ingredient in strong_seasonal:
                    off_season.append(ingredient)

        # Calculate score
        if matching:
            base_score = 0.8  # Seasonal ingredient bonus
        else:
            base_score = 0.5  # Neutral

        # Penalty for off-season ingredients
        if off_season:
            base_score -= 0.3 * len(off_season)

        score = max(0.0, min(1.0, base_score))

        return SeasonalScore(
            meal_id=meal.id,
            meal_name=meal.name,
            score=score,
            season=season,
            matching_ingredients=matching,
            off_season_ingredients=off_season,
        )

    def score_meals(
        self,
        meals: list["Meal"],
        season: str | None = None,
    ) -> list[SeasonalScore]:
        """Score multiple meals for seasonality.

        Args:
            meals: List of meals to score
            season: Season to score against

        Returns:
            List of SeasonalScore objects, sorted by score descending
        """
        scores = [self.score_meal(meal, season) for meal in meals]
        return sorted(scores, key=lambda s: s.score, reverse=True)

    def get_seasonal_meals(
        self,
        meals: list["Meal"],
        season: str | None = None,
        min_score: float = 0.5,
    ) -> list["Meal"]:
        """Filter meals to only seasonal ones.

        Args:
            meals: List of meals to filter
            season: Season to check
            min_score: Minimum seasonality score

        Returns:
            List of meals that are seasonal
        """
        scores = self.score_meals(meals, season)
        score_map = {s.meal_id: s for s in scores}

        return [
            meal for meal in meals
            if score_map[meal.id].score >= min_score
        ]

    def suggest_for_season(
        self,
        season: str | None = None,
    ) -> dict[str, list[str]]:
        """Get ingredient suggestions for a season.

        Args:
            season: Season to get suggestions for

        Returns:
            Dict with ingredient categories
        """
        if season is None:
            season = get_current_season()

        region_data = self.data.get("hungary", {})
        season_data = region_data.get(season, {})

        return {
            "vegetables": season_data.get("vegetables", []),
            "fruits": season_data.get("fruits", []),
            "herbs": season_data.get("herbs", []),
        }
