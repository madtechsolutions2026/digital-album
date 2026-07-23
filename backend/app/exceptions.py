"""Custom exception classes for the AI Wedding Photo Portal backend.

This module defines application-specific exceptions with error codes
for structured error handling and consistent API responses.
"""


class AppException(Exception):
    """Base exception for all application errors.
    
    All custom exceptions inherit from this base class and include
    both a human-readable message and a machine-readable error code.
    
    Attributes:
        message: Human-readable error description
        code: Machine-readable error code (e.g., 'VALIDATION_ERROR')
    """
    
    def __init__(self, message: str, code: str):
        """Initialize AppException with message and error code.
        
        Args:
            message: Human-readable error description
            code: Machine-readable error code
        """
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(AppException):
    """Raised when input validation fails.
    
    Examples:
        - File size exceeds 10MB limit
        - Invalid image format
        - Image dimensions exceed maximum
        - Missing required fields
    """
    
    def __init__(self, message: str):
        """Initialize ValidationError with error message.
        
        Args:
            message: Description of the validation failure
        """
        super().__init__(message, "VALIDATION_ERROR")


class EventNotFoundError(AppException):
    """Raised when event_id doesn't exist in the database.
    
    This exception is raised when attempting to upload photos to
    or search photos from a non-existent event.
    """
    
    def __init__(self, event_id: int):
        """Initialize EventNotFoundError with event ID.
        
        Args:
            event_id: The ID of the event that was not found
        """
        super().__init__(f"Event {event_id} not found", "EVENT_NOT_FOUND")
        self.event_id = event_id


class FaceDetectionError(AppException):
    """Raised when face detection fails.
    
    Examples:
        - InsightFace model fails to process image
        - Image format incompatible with face detection
        - No face detected in selfie during search
    """
    
    def __init__(self, message: str):
        """Initialize FaceDetectionError with error message.
        
        Args:
            message: Description of the face detection failure
        """
        super().__init__(message, "FACE_DETECTION_ERROR")


class UnauthorizedError(AppException):
    """Raised when a gallery request has no valid access token.

    Examples:
        - No Authorization header on a gallery-scoped request
        - Access token is malformed, expired, or has an invalid signature
    """

    def __init__(self, message: str = "Missing or invalid access token"):
        super().__init__(message, "UNAUTHORIZED")


class ForbiddenError(AppException):
    """Raised when a valid access token doesn't authorize the requested event.

    Examples:
        - A token scoped to event 5 is used to request event 7's photos
    """

    def __init__(self, message: str = "Not authorized for this event"):
        super().__init__(message, "FORBIDDEN")


class DatabaseError(AppException):
    """Raised when database operations fail.
    
    Examples:
        - Connection pool exhausted
        - Query execution timeout
        - Constraint violation
        - Transaction rollback failure
    """
    
    def __init__(self, message: str):
        """Initialize DatabaseError with error message.
        
        Args:
            message: Description of the database failure
        """
        super().__init__(message, "DATABASE_ERROR")
