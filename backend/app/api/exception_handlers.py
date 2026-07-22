"""
FastAPI exception handlers.

This module defines exception handlers that convert application exceptions
into appropriate HTTP responses with consistent JSON structure.
"""

import logging
from typing import Any, Dict

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions import (
    AppException,
    ValidationError,
    EventNotFoundError,
    FaceDetectionError,
    DatabaseError
)


logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    message: str,
    error_code: str,
    details: Dict[str, Any] = None,
    request_id: str = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Optional additional error details
        request_id: Optional request ID for correlation
        
    Returns:
        JSONResponse with error structure
    """
    content = {
        "success": False,
        "message": message,
        "error": {
            "code": error_code,
            "details": details or {}
        }
    }
    
    if request_id:
        content["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle ValidationError exceptions.
    
    Returns 400 Bad Request with error details.
    
    Args:
        request: The FastAPI request
        exc: The ValidationError exception
        
    Returns:
        JSONResponse with 400 status
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(
        f"Validation error: {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.code,
            "path": request.url.path
        }
    )
    
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message=exc.message,
        error_code=exc.code,
        request_id=request_id
    )


async def event_not_found_handler(request: Request, exc: EventNotFoundError) -> JSONResponse:
    """
    Handle EventNotFoundError exceptions.
    
    Returns 404 Not Found with error details.
    
    Args:
        request: The FastAPI request
        exc: The EventNotFoundError exception
        
    Returns:
        JSONResponse with 404 status
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(
        f"Event not found: {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.code,
            "event_id": exc.event_id,
            "path": request.url.path
        }
    )
    
    return create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        message=exc.message,
        error_code=exc.code,
        details={"event_id": exc.event_id},
        request_id=request_id
    )


async def face_detection_error_handler(request: Request, exc: FaceDetectionError) -> JSONResponse:
    """
    Handle FaceDetectionError exceptions.
    
    Returns 400 Bad Request for client-side issues (no face detected)
    or 500 Internal Server Error for system issues.
    
    Args:
        request: The FastAPI request
        exc: The FaceDetectionError exception
        
    Returns:
        JSONResponse with appropriate status code
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Determine if this is a client error or server error
    # If message contains "No face detected", it's a client error (400)
    # Otherwise it's a server error (500)
    if "no face" in exc.message.lower() or "not detected" in exc.message.lower():
        status_code = status.HTTP_400_BAD_REQUEST
        log_level = logging.WARNING
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        log_level = logging.ERROR
    
    logger.log(
        log_level,
        f"Face detection error: {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.code,
            "path": request.url.path
        }
    )
    
    return create_error_response(
        status_code=status_code,
        message=exc.message,
        error_code=exc.code,
        request_id=request_id
    )


async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """
    Handle DatabaseError exceptions.
    
    Returns 503 Service Unavailable with Retry-After header.
    
    Args:
        request: The FastAPI request
        exc: The DatabaseError exception
        
    Returns:
        JSONResponse with 503 status and Retry-After header
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"Database error: {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.code,
            "path": request.url.path
        }
    )
    
    response = create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message="Database service temporarily unavailable. Please try again later.",
        error_code=exc.code,
        request_id=request_id
    )
    
    # Add Retry-After header suggesting retry in 60 seconds
    response.headers["Retry-After"] = "60"
    
    return response


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle uncaught SQLAlchemy exceptions.
    
    This is a catch-all for database errors that weren't wrapped
    in our DatabaseError exception.
    
    Returns 503 Service Unavailable with Retry-After header.
    
    Args:
        request: The FastAPI request
        exc: The SQLAlchemyError exception
        
    Returns:
        JSONResponse with 503 status
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"Uncaught SQLAlchemy error: {str(exc)}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.url.path
        }
    )
    
    response = create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message="Database service temporarily unavailable. Please try again later.",
        error_code="DATABASE_ERROR",
        request_id=request_id
    )
    
    response.headers["Retry-After"] = "60"
    
    return response


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle uncaught generic exceptions.
    
    Returns 500 Internal Server Error without exposing internal details.
    
    Args:
        request: The FastAPI request
        exc: The generic Exception
        
    Returns:
        JSONResponse with 500 status
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "exception_type": type(exc).__name__
        }
    )
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred. Please try again later.",
        error_code="INTERNAL_SERVER_ERROR",
        request_id=request_id
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle generic AppException (catch-all for custom exceptions).
    
    Returns 500 Internal Server Error by default.
    
    Args:
        request: The FastAPI request
        exc: The AppException
        
    Returns:
        JSONResponse with 500 status
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.code,
            "path": request.url.path
        }
    )
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=exc.message,
        error_code=exc.code,
        request_id=request_id
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Register custom exception handlers
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(EventNotFoundError, event_not_found_handler)
    app.add_exception_handler(FaceDetectionError, face_detection_error_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    
    # Register SQLAlchemy exception handler
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    
    # Register generic exception handler (must be last)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")
