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
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.config import get_settings
from app.logging_config import setup_logging
from app.middleware import RequestIDMiddleware
from app.api.exception_handlers import register_exception_handlers
from app.api.routes import photos_router, events_router, jobs_router
from app.api.schemas import HealthCheckResponse, HealthCheckData
from app.services import get_face_service
from app.database import close_db, get_db


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
        
        # Initialize and load InsightFace model
        logger.info("Loading InsightFace model...")
        face_service = get_face_service()
        logger.info("InsightFace model loaded successfully")
        
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
        
        ## Authentication
        
        This version does not include authentication. Authentication should be added
        before deploying to production.
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
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
    logger.info("API routers registered")
    
    # Mount static files for photo serving
    # Mount the photos subdirectory since STORAGE_PATH points to storage/photos
    storage_path = settings.STORAGE_PATH
    if not os.path.isabs(storage_path):
        storage_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), storage_path)
    os.makedirs(storage_path, exist_ok=True)
    app.mount("/storage", StaticFiles(directory=storage_path), name="storage")
    logger.info(f"Static files mounted at /storage from {storage_path}")
    
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
    return {
        "name": "AI Wedding Photo Portal API",
        "version": "1.0.0",
        "description": "FastAPI backend for AI-powered wedding photo matching",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/health"
    }


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
