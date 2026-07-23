"""API route handlers."""

from app.api.routes.photos import router as photos_router
from app.api.routes.events import router as events_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.gallery import router as gallery_router

__all__ = ["photos_router", "events_router", "jobs_router", "gallery_router"]
