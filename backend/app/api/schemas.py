"""
API request and response schemas.

This module defines Pydantic models for API requests and responses,
ensuring consistent structure across all endpoints.
"""

from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Generic type for response data
T = TypeVar('T')


class BaseResponse(BaseModel):
    """
    Base response model with common fields.
    
    All API responses include:
    - success: Boolean indicating if request was successful
    - message: Human-readable message describing the result
    """
    
    success: bool = Field(
        ...,
        description="Whether the request was successful"
    )
    message: str = Field(
        ...,
        description="Human-readable message describing the result"
    )
    
    class Config:
        """Pydantic configuration."""
        # Use snake_case for all field names
        populate_by_name = True


class SuccessResponse(BaseResponse, Generic[T]):
    """
    Success response with data payload.
    
    Generic response for successful operations that return data.
    """
    
    success: bool = Field(
        default=True,
        description="Always true for success responses"
    )
    data: T = Field(
        ...,
        description="Response data payload"
    )


class ErrorDetail(BaseModel):
    """
    Error detail information.
    
    Contains machine-readable error code and optional details.
    """
    
    code: str = Field(
        ...,
        description="Machine-readable error code"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error details"
    )


class ErrorResponse(BaseResponse):
    """
    Error response with error information.
    
    Returned when an error occurs during request processing.
    """
    
    success: bool = Field(
        default=False,
        description="Always false for error responses"
    )
    error: ErrorDetail = Field(
        ...,
        description="Error information"
    )


# Photo Upload Response Models

class PhotoUploadData(BaseModel):
    """
    Data returned from photo upload operation.
    
    Contains information about the uploaded photo and detected faces.
    """
    
    photo_id: int = Field(
        ...,
        description="ID of the created photo record"
    )
    file_path: str = Field(
        ...,
        description="Relative path to the stored image file"
    )
    face_count: int = Field(
        ...,
        description="Number of faces detected in the photo"
    )
    faces_stored: int = Field(
        ...,
        description="Number of face embeddings stored in database"
    )
    warning: Optional[str] = Field(
        None,
        description="Optional warning message (e.g., no faces detected)"
    )


class PhotoUploadResponse(SuccessResponse[PhotoUploadData]):
    """
    Response for photo upload endpoint.
    
    Example:
        {
            "success": true,
            "message": "Photo uploaded successfully with 3 faces detected",
            "data": {
                "photo_id": 123,
                "file_path": "event_1/abc123.jpg",
                "face_count": 3,
                "faces_stored": 3,
                "warning": null
            }
        }
    """
    pass


# Face Search Response Models

class BoundingBox(BaseModel):
    """Face bounding box coordinates."""
    
    x1: float = Field(..., description="Left coordinate")
    y1: float = Field(..., description="Top coordinate")
    x2: float = Field(..., description="Right coordinate")
    y2: float = Field(..., description="Bottom coordinate")


class PhotoMatch(BaseModel):
    """
    A photo that matches the search query.
    
    Contains photo information and similarity metrics.
    """
    
    photo_id: int = Field(
        ...,
        description="ID of the matching photo"
    )
    file_path: str = Field(
        ...,
        description="Relative path to the photo file"
    )
    embedding_id: int = Field(
        ...,
        description="ID of the matching face embedding"
    )
    bounding_box: BoundingBox = Field(
        ...,
        description="Bounding box of the detected face"
    )
    confidence_score: float = Field(
        ...,
        description="Face detection confidence score (0.0 to 1.0)"
    )
    similarity_score: float = Field(
        ...,
        description="Face similarity score (0.0 to 1.0, higher is more similar)"
    )


class FaceSearchData(BaseModel):
    """
    Data returned from face search operation.
    
    Contains matching photos and search metadata.
    """
    
    matches: List[PhotoMatch] = Field(
        ...,
        description="List of matching photos ordered by similarity"
    )
    num_matches: int = Field(
        ...,
        description="Total number of matches found"
    )
    query_face_confidence: float = Field(
        ...,
        description="Confidence score of the face detected in the query selfie"
    )
    threshold_used: float = Field(
        ...,
        description="Similarity threshold used for the search"
    )


class FaceSearchResponse(SuccessResponse[FaceSearchData]):
    """
    Response for face search endpoint.
    
    Example:
        {
            "success": true,
            "message": "Found 15 matching photos",
            "data": {
                "matches": [
                    {
                        "photo_id": 123,
                        "file_path": "event_1/abc123.jpg",
                        "embedding_id": 456,
                        "bounding_box": {"x1": 100, "y1": 150, "x2": 300, "y2": 400},
                        "confidence_score": 0.98,
                        "similarity_score": 0.92
                    }
                ],
                "num_matches": 15,
                "query_face_confidence": 0.95,
                "threshold_used": 0.6
            }
        }
    """
    pass


# Health Check Response Models

class HealthCheckData(BaseModel):
    """
    Health check status data.
    
    Indicates the health status of the service and its dependencies.
    """
    
    status: str = Field(
        ...,
        description="Overall health status: 'healthy' or 'unhealthy'"
    )
    database: str = Field(
        ...,
        description="Database connection status: 'connected' or 'disconnected'"
    )
    version: str = Field(
        default="1.0.0",
        description="API version"
    )


class HealthCheckResponse(BaseResponse):
    """
    Response for health check endpoint.
    
    Example (healthy):
        {
            "success": true,
            "message": "Service is healthy",
            "data": {
                "status": "healthy",
                "database": "connected",
                "version": "1.0.0"
            }
        }
    
    Example (unhealthy):
        {
            "success": false,
            "message": "Service is unhealthy",
            "data": {
                "status": "unhealthy",
                "database": "disconnected",
                "version": "1.0.0"
            }
        }
    """
    
    data: HealthCheckData = Field(
        ...,
        description="Health check data"
    )
