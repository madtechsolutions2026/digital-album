"""Unit tests for custom exception classes."""

import pytest
from app.exceptions import (
    AppException,
    ValidationError,
    EventNotFoundError,
    FaceDetectionError,
    DatabaseError
)


class TestAppException:
    """Tests for the base AppException class."""
    
    def test_app_exception_attributes(self):
        """Test that AppException stores message and code correctly."""
        exc = AppException("Test error", "TEST_ERROR")
        assert exc.message == "Test error"
        assert exc.code == "TEST_ERROR"
        assert str(exc) == "Test error"
    
    def test_app_exception_inheritance(self):
        """Test that AppException inherits from Exception."""
        exc = AppException("Test", "TEST")
        assert isinstance(exc, Exception)


class TestValidationError:
    """Tests for ValidationError exception."""
    
    def test_validation_error_message(self):
        """Test that ValidationError has correct message and code."""
        exc = ValidationError("File size exceeds 10MB limit")
        assert exc.message == "File size exceeds 10MB limit"
        assert exc.code == "VALIDATION_ERROR"
    
    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from AppException."""
        exc = ValidationError("Test validation error")
        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)
    
    def test_validation_error_can_be_raised(self):
        """Test that ValidationError can be raised and caught."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid input")
        assert exc_info.value.message == "Invalid input"
        assert exc_info.value.code == "VALIDATION_ERROR"


class TestEventNotFoundError:
    """Tests for EventNotFoundError exception."""
    
    def test_event_not_found_error_message(self):
        """Test that EventNotFoundError formats message with event_id."""
        exc = EventNotFoundError(123)
        assert exc.message == "Event 123 not found"
        assert exc.code == "EVENT_NOT_FOUND"
        assert exc.event_id == 123
    
    def test_event_not_found_error_inheritance(self):
        """Test that EventNotFoundError inherits from AppException."""
        exc = EventNotFoundError(456)
        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)
    
    def test_event_not_found_error_different_ids(self):
        """Test that different event IDs produce different messages."""
        exc1 = EventNotFoundError(1)
        exc2 = EventNotFoundError(999)
        assert exc1.message == "Event 1 not found"
        assert exc2.message == "Event 999 not found"
        assert exc1.event_id == 1
        assert exc2.event_id == 999


class TestFaceDetectionError:
    """Tests for FaceDetectionError exception."""
    
    def test_face_detection_error_message(self):
        """Test that FaceDetectionError has correct message and code."""
        exc = FaceDetectionError("No face detected in image")
        assert exc.message == "No face detected in image"
        assert exc.code == "FACE_DETECTION_ERROR"
    
    def test_face_detection_error_inheritance(self):
        """Test that FaceDetectionError inherits from AppException."""
        exc = FaceDetectionError("Test error")
        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)
    
    def test_face_detection_error_can_be_raised(self):
        """Test that FaceDetectionError can be raised and caught."""
        with pytest.raises(FaceDetectionError) as exc_info:
            raise FaceDetectionError("InsightFace model failed")
        assert exc_info.value.message == "InsightFace model failed"
        assert exc_info.value.code == "FACE_DETECTION_ERROR"


class TestDatabaseError:
    """Tests for DatabaseError exception."""
    
    def test_database_error_message(self):
        """Test that DatabaseError has correct message and code."""
        exc = DatabaseError("Connection pool exhausted")
        assert exc.message == "Connection pool exhausted"
        assert exc.code == "DATABASE_ERROR"
    
    def test_database_error_inheritance(self):
        """Test that DatabaseError inherits from AppException."""
        exc = DatabaseError("Test error")
        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)
    
    def test_database_error_can_be_raised(self):
        """Test that DatabaseError can be raised and caught."""
        with pytest.raises(DatabaseError) as exc_info:
            raise DatabaseError("Transaction rollback failed")
        assert exc_info.value.message == "Transaction rollback failed"
        assert exc_info.value.code == "DATABASE_ERROR"


class TestExceptionHierarchy:
    """Tests for exception hierarchy and polymorphism."""
    
    def test_all_custom_exceptions_inherit_from_app_exception(self):
        """Test that all custom exceptions can be caught as AppException."""
        exceptions = [
            ValidationError("test"),
            EventNotFoundError(1),
            FaceDetectionError("test"),
            DatabaseError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, AppException)
    
    def test_catching_app_exception_catches_all_custom_exceptions(self):
        """Test that catching AppException catches all subclasses."""
        # ValidationError
        with pytest.raises(AppException):
            raise ValidationError("test")
        
        # EventNotFoundError
        with pytest.raises(AppException):
            raise EventNotFoundError(1)
        
        # FaceDetectionError
        with pytest.raises(AppException):
            raise FaceDetectionError("test")
        
        # DatabaseError
        with pytest.raises(AppException):
            raise DatabaseError("test")
    
    def test_exception_codes_are_unique(self):
        """Test that each exception type has a unique error code."""
        codes = {
            ValidationError("test").code,
            EventNotFoundError(1).code,
            FaceDetectionError("test").code,
            DatabaseError("test").code
        }
        assert len(codes) == 4  # All codes should be unique
