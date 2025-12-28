"""Analytics API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from carmy.api.deps import get_db
from carmy.services.analytics import AnalyticsService

router = APIRouter()


@router.get("/report")
def get_full_report(db: Session = Depends(get_db)) -> dict:
    """Get a complete analytics report."""
    service = AnalyticsService(db)
    report = service.generate_full_report()

    return {
        "generated_date": report.generated_date.isoformat(),
        "frequency": {
            "total_meals": report.frequency.total_meals,
            "total_uses": report.frequency.total_uses,
            "average_uses_per_meal": report.frequency.average_uses_per_meal,
            "most_used": report.frequency.most_used[:10],
            "never_used_count": len(report.frequency.never_used),
        },
        "cuisine": {
            "total_meals_with_cuisine": report.cuisine.total_meals_with_cuisine,
            "top_cuisines": report.cuisine.top_cuisines[:10],
        },
        "patterns": {
            "meals_per_week_avg": report.patterns.meals_per_week_avg,
            "soups_per_week_avg": report.patterns.soups_per_week_avg,
            "mains_per_week_avg": report.patterns.mains_per_week_avg,
            "meat_per_week_avg": report.patterns.meat_per_week_avg,
            "vegetarian_per_week_avg": report.patterns.vegetarian_per_week_avg,
        },
        "leftovers": {
            "total_leftovers": report.leftovers.total_leftovers,
            "total_meals": report.leftovers.total_meals,
            "leftover_percentage": report.leftovers.leftover_percentage,
        },
    }


@router.get("/frequency")
def get_frequency_report(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    """Get meal frequency statistics."""
    service = AnalyticsService(db)
    report = service.get_frequency_report(limit=limit)

    return {
        "total_meals": report.total_meals,
        "total_uses": report.total_uses,
        "average_uses_per_meal": report.average_uses_per_meal,
        "most_used": report.most_used,
        "least_used": report.least_used,
        "never_used": report.never_used,
    }


@router.get("/cuisines")
def get_cuisine_report(db: Session = Depends(get_db)) -> dict:
    """Get cuisine distribution statistics."""
    service = AnalyticsService(db)
    report = service.get_cuisine_report()

    return {
        "total_meals_with_cuisine": report.total_meals_with_cuisine,
        "distribution": report.distribution,
        "percentages": report.percentages,
        "top_cuisines": report.top_cuisines,
    }


@router.get("/types")
def get_type_report(db: Session = Depends(get_db)) -> dict:
    """Get meal type distribution statistics."""
    service = AnalyticsService(db)
    report = service.get_type_report()

    return {
        "distribution": report.distribution,
        "percentages": report.percentages,
    }


@router.get("/patterns")
def get_pattern_report(db: Session = Depends(get_db)) -> dict:
    """Get eating pattern statistics."""
    service = AnalyticsService(db)
    report = service.get_pattern_report()

    return {
        "meals_per_week_avg": report.meals_per_week_avg,
        "soups_per_week_avg": report.soups_per_week_avg,
        "mains_per_week_avg": report.mains_per_week_avg,
        "meat_per_week_avg": report.meat_per_week_avg,
        "vegetarian_per_week_avg": report.vegetarian_per_week_avg,
        "weekly_trends": report.weekly_trends[-12:],  # Last 12 weeks
    }


@router.get("/trends")
def get_trends(
    weeks: int = Query(12, ge=1, le=52),
    db: Session = Depends(get_db),
) -> dict:
    """Get trends over recent weeks."""
    service = AnalyticsService(db)
    return service.get_trends(weeks=weeks)
