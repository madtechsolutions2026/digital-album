"""
Request ID middleware for FastAPI.

This middleware generates or extracts a unique request ID for each HTTP request
and adds it to the request state and response headers for request tracing and correlation.
"""

import uuid
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.logging_config import add_request_id_to_logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds request ID tracking to all HTTP requests.
    
    Features:
    - Extracts X-Request-ID header if present, or generates a new UUID
    - Adds request_id to request.state for access in route handlers
    - Adds X-Request-ID to response headers
    - Integrates with logging system for request correlation
    """
    
    REQUEST_ID_HEADER = "X-Request-ID"
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and add request ID tracking.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            Response with X-Request-ID header added
        """
        # Extract request ID from header or generate new one
        request_id = request.headers.get(self.REQUEST_ID_HEADER)
        
        if not request_id:
            # Generate new UUID v4 if no request ID provided
            request_id = str(uuid.uuid4())
        
        # Add request_id to request state for access in route handlers
        request.state.request_id = request_id
        
        # Add request ID to logger context for this request
        logger = logging.getLogger("app")
        add_request_id_to_logger(logger, request_id)
        
        # Log the incoming request
        self.logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None,
            }
        )
        
        # Process the request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log unhandled exceptions with request ID
            self.logger.error(
                f"Unhandled exception during request: {str(e)}",
                exc_info=True,
                extra={"request_id": request_id}
            )
            raise
        
        # Add request ID to response headers
        response.headers[self.REQUEST_ID_HEADER] = request_id
        
        # Log the response
        self.logger.info(
            f"Response: {response.status_code}",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
            }
        )
        
        return response


def get_request_id(request: Request) -> str:
    """
    Helper function to get request ID from request state.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The request ID string, or 'N/A' if not present
    """
    return getattr(request.state, "request_id", "N/A")
