"""
Main FastAPI application.

This module initializes and configures the FastAPI application with:
- API metadata and documentation
- CORS middleware
- Request ID middleware
- Exception handlers
- API routers
- Startup/shutdown events
"""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.config import get_settings
from app.logging_config import setup_logging
from app.middleware import RequestIDMiddleware
from app.middleware.photographer_access import PhotographerAccessMiddleware
from app.api.exception_handlers import register_exception_handlers
from app.api.routes import photos_router, events_router, jobs_router, gallery_router, guests_router
from app.api.schemas import HealthCheckResponse, HealthCheckData
from app.database import close_db, get_db
from app.models.photo import Photo
from app.services.auth import decode_gallery_token


# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Startup:
    - Load InsightFace model
    - Validate environment configuration
    
    Shutdown:
    - Close database connections
    - Cleanup resources
    """
    # Startup
    logger.info("Starting AI Wedding Photo Portal backend...")
    
    try:
        # Validate settings
        settings = get_settings()
        logger.info(f"Configuration loaded: DATABASE_URL configured, DEBUG={settings.DEBUG}")

        # InsightFace model is loaded lazily on first use (see
        # get_face_service) rather than here, so the app can start and pass
        # health checks without waiting on the ~600MB model download/load.

        # Log startup complete
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    try:
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)
    
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()
    
    # Create FastAPI app with metadata
    app = FastAPI(
        title="AI Wedding Photo Portal",
        version="1.0.0",
        description="""
        FastAPI backend for AI-powered wedding photo matching using face recognition.
        
        ## Features
        
        * **Photo Upload**: Upload photos to events with automatic face detection
        * **Face Search**: Find all photos containing a specific person using a selfie
        * **Vector Similarity**: Fast face matching using PostgreSQL pgvector
        * **InsightFace**: High-quality face detection and embedding generation
        
        ## Endpoints
        
        * `POST /api/photos/upload` - Upload a photo to an event
        * `POST /api/photos/search` - Search for photos by face similarity
        * `GET /health` - Health check endpoint
        
        ## Access

        Public product pages are available to everyone. Photographer event management
        requires a studio sign-in, and each guest gallery requires its event code and
        password.
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # Keep compatibility with the existing Railway credentials while the
    # photographer studio credentials are migrated to their product names.
    studio_username = os.environ.get("ADMIN_USERNAME") or os.environ.get("DEMO_USERNAME") or "photographer"
    studio_password = os.environ.get("ADMIN_PASSWORD") or os.environ.get("DEMO_PASSWORD", "")
    app.add_middleware(
        PhotographerAccessMiddleware,
        username=studio_username,
        password=studio_password,
    )
    
    # Configure CORS
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID"]
        )
        logger.info(f"CORS enabled for origins: {settings.CORS_ORIGINS}")
    
    # Add Request ID middleware
    app.add_middleware(RequestIDMiddleware)
    logger.info("Request ID middleware added")
    
    # Configure request size limits (11MB to allow 10MB images + overhead)
    app.router.default_response_class.max_size = 11 * 1024 * 1024
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Include API routers
    app.include_router(photos_router)
    app.include_router(events_router)
    app.include_router(jobs_router)
    app.include_router(gallery_router)
    app.include_router(guests_router)
    logger.info("API routers registered")
    
    # Mount static files for photo serving
    # Mount the photos subdirectory since STORAGE_PATH points to storage/photos
    storage_path = settings.STORAGE_PATH
    if not os.path.isabs(storage_path):
        storage_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), storage_path)
    storage_root = Path(storage_path).resolve()
    storage_root.mkdir(parents=True, exist_ok=True)

    @app.get("/storage/{relative_path:path}", include_in_schema=False)
    async def serve_private_photo(
        relative_path: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
    ):
        # Allow selfies, studio access, or valid gallery token
        is_selfie = relative_path.startswith("selfies/") or "selfie" in relative_path
        has_studio = request.cookies.get("dg_studio_access") is not None
        event_id = decode_gallery_token(request.cookies.get("dg_gallery_access", ""))
        if not (is_selfie or has_studio or event_id is not None or settings.DEBUG):
            raise HTTPException(status_code=401, detail="Unlock this gallery to view its photos.")

        result = await db.execute(select(Photo.event_id).where(Photo.file_path == relative_path))
        photo_event_id = result.scalar_one_or_none()
        if photo_event_id is None or photo_event_id != event_id:
            raise HTTPException(status_code=404, detail="Photo not found.")

        photo_path = (storage_root / relative_path).resolve()
        if not photo_path.is_relative_to(storage_root) or not photo_path.is_file():
            raise HTTPException(status_code=404, detail="Photo not found.")
        return FileResponse(photo_path)

    logger.info(f"Private photo files served from {storage_root}")
    
    # Add health check endpoint at root level
    @app.get(
        "/health",
        response_model=HealthCheckResponse,
        tags=["health"],
        summary="Health check endpoint"
    )
    async def health_check(db: AsyncSession = Depends(get_db)) -> HealthCheckResponse:
        """Check service health and database connectivity."""
        db_status = "connected"
        service_healthy = True
        
        try:
            result = await db.execute(text("SELECT 1"))
            result.scalar()
            logger.info("Health check: database connected")
        except Exception as e:
            db_status = "disconnected"
            service_healthy = False
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
        
        overall_status = "healthy" if service_healthy else "unhealthy"
        message = "Service is healthy" if service_healthy else "Service is unhealthy"
        
        return HealthCheckResponse(
            success=service_healthy,
            message=message,
            data=HealthCheckData(
                status=overall_status,
                database=db_status,
                version="1.0.0"
            )
        )
    
    return app


# Create application instance
app = create_app()


# Root endpoint
@app.get(
    "/",
    tags=["root"],
    summary="API root endpoint",
    description="Returns basic API information and links to documentation"
)
async def root():
    """
    Root endpoint providing API information.
    
    Returns:
        Dictionary with API name, version, and documentation links
    """
    frontend = os.environ.get("FRONTEND_DIST")
    if frontend:
        from starlette.responses import FileResponse
        return FileResponse(os.path.join(frontend, "index.html"))
    return {
        "name": "AI Wedding Photo Portal API",
        "version": "1.0.0",
        "description": "FastAPI backend for AI-powered wedding photo matching",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/health"
    }


if os.environ.get("FRONTEND_DIST"):
    from pathlib import Path
    from starlette.responses import FileResponse
    from fastapi import HTTPException

    @app.get("/{frontend_path:path}", include_in_schema=False)
    async def frontend_page(frontend_path: str):
        if frontend_path.startswith(("api/", "storage/")):
            raise HTTPException(404)
        base = Path(os.environ["FRONTEND_DIST"]).resolve()
        target = (base / frontend_path).resolve()
        if not target.is_relative_to(base):
            raise HTTPException(404)
        if target.is_file():
            return FileResponse(target)
        index_file = base / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        raise HTTPException(404)


if __name__ == "__main__":
    # This block is only executed when running the file directly
    # For production, use uvicorn command or gunicorn
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
