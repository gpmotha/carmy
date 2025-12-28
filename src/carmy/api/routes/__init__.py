"""API routes for Carmy."""

from fastapi import APIRouter

from carmy.api.routes.meals import router as meals_router
from carmy.api.routes.plans import router as plans_router
from carmy.api.routes.analytics import router as analytics_router
from carmy.api.routes.export import router as export_router
from carmy.api.routes.board import router as board_router
# v2 routes
from carmy.api.routes.months import router as months_router
from carmy.api.routes.weeks import router as weeks_router

api_router = APIRouter()

api_router.include_router(meals_router, prefix="/meals", tags=["meals"])
api_router.include_router(plans_router, prefix="/plans", tags=["plans"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(export_router, prefix="/export", tags=["export"])
api_router.include_router(board_router)
# v2 routes
api_router.include_router(months_router)
api_router.include_router(weeks_router)
