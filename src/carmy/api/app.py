"""FastAPI application for Carmy Web UI."""

from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from carmy import __version__
from carmy.api.routes import api_router
from carmy.api.routes.pages import router as pages_router
from carmy.api.routes.htmx import router as htmx_router

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Create FastAPI app
app = FastAPI(
    title="Carmy",
    description="A smart weekly meal planner for families",
    version=__version__,
)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Set up templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# Include API routes
app.include_router(api_router, prefix="/api")

# Include page routes (HTML)
app.include_router(pages_router)

# Include HTMX routes
app.include_router(htmx_router, prefix="/htmx")


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "date": date.today().isoformat(),
    }
